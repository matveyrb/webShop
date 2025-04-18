from urllib.parse import urlparse

from flask import Blueprint
from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import current_user, login_user, logout_user, login_required

from app import db
from app.forms import LoginForm, RegistrationForm, CheckoutForm, EditProfileForm
from app.models import User, Product, Order
from app.utils.stats_utils import (
    get_visit_stats,
    get_sales_stats,
    get_popular_products,
    get_conversion_rate
)

# Main Blueprint
main_bp = Blueprint('main', __name__)
# Auth Blueprint
auth_bp = Blueprint('auth', __name__)
# Products Blueprint
products_bp = Blueprint('products', __name__)
# Cart Blueprint
cart_bp = Blueprint('cart', __name__)


@main_bp.route('/')
def index():
    """Главная страница интернет-магазина"""
    featured_products = Product.query.order_by(Product.created_at.desc()).limit(3).all()
    return render_template('index.html', featured_products=featured_products)


@products_bp.route('/catalog')
def catalog():
    """Страница каталога товаров с фильтрацией и сортировкой"""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    category = request.args.get('category', '')
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    sort = request.args.get('sort', 'newest')

    # Базовый запрос
    query = Product.query

    # Применяем фильтры
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))

    if category:
        query = query.filter_by(category=category)

    if price_min is not None:
        query = query.filter(Product.price >= price_min)

    if price_max is not None:
        query = query.filter(Product.price <= price_max)

    # Применяем сортировку
    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'name_asc':
        query = query.order_by(Product.name.asc())
    elif sort == 'name_desc':
        query = query.order_by(Product.name.desc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())

    # Получаем уникальные категории для фильтров
    categories = db.session.query(Product.category.distinct()).all()
    categories = [c[0] for c in categories]

    # Пагинация
    products = query.paginate(page=page, per_page=6, error_out=False)

    return render_template('catalog.html',
                           products=products,
                           categories=categories)


@products_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Страница с подробной информацией о товаре"""
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)


@cart_bp.route('/cart')
@login_required
def view_cart():
    """Страница корзины пользователя"""
    from app.models import CartItem  # Локальный импорт для избежания циклических зависимостей

    # Получаем все товары в корзине для текущего пользователя
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    # Добавляем связанные продукты через join для оптимизации запросов
    cart_items = (CartItem.query
                  .filter_by(user_id=current_user.id)
                  .join(Product)
                  .all())

    # Вычисляем общую сумму
    total = sum(item.product.price * item.quantity for item in cart_items)

    return render_template('cart.html',
                           cart_items=cart_items,
                           total=total,
                           cart_count=current_user.get_cart_count())


@cart_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    from app.models import CartItem  # Локальный импорт

    product = Product.query.get_or_404(product_id)
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(cart_item)

    db.session.commit()
    return jsonify({
        'success': True,
        'cart_count': current_user.get_cart_count()  # Используем метод get_cart_count()
    })


@cart_bp.route('/cart/update/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    from app.models import CartItem

    data = request.get_json()
    action = data.get('action')

    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not cart_item:
        return jsonify({'success': False})

    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease' and cart_item.quantity > 1:
        cart_item.quantity -= 1

    db.session.commit()
    return jsonify({'success': True})


@cart_bp.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    from app.models import CartItem

    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()

    return jsonify({
        'success': True,
        'cart_count': current_user.get_cart_count()  # Возвращаем обновленное количество
    })


@cart_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Страница оформления заказа"""
    from app.models import CartItem, Order, OrderItem, Product

    form = CheckoutForm()

    # Получаем товары в корзине с join для оптимизации
    cart_items = (CartItem.query
                  .filter_by(user_id=current_user.id)
                  .join(Product)
                  .all())

    total = sum(item.product.price * item.quantity for item in cart_items)

    # Если корзина пуста, перенаправляем обратно
    if not cart_items:
        flash('Ваша корзина пуста', 'warning')
        return redirect(url_for('cart.view_cart'))

    # Обработка отправки формы
    if request.method == 'POST':
            try:
                # Создаем заказ
                order = Order(
                    user_id=current_user.id,
                    total=total,
                    status='pending'
                )

                db.session.add(order)
                db.session.flush()  # Получаем ID заказа перед созданием OrderItem

                # Добавляем товары из корзины в заказ
                for item in cart_items:
                    # Проверка наличия товара на складе
                    if item.product.stock < item.quantity:
                        raise ValueError(f'Недостаточно товара "{item.product.name}" на складе')

                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        price=item.product.price
                    )
                    db.session.add(order_item)

                    # Обновляем количество товара на складе
                    item.product.stock -= item.quantity

                    # Удаляем из корзины
                    db.session.delete(item)

                db.session.commit()
                flash('Ваш заказ успешно оформлен!', 'success')
                return redirect(url_for('main.order_detail', order_id=order.id))

            except ValueError as e:
                db.session.rollback()
                flash(str(e), 'error')

    # Заполняем форму данными пользователя (только для GET-запроса)
    if request.method == 'GET':
        if current_user.is_authenticated:
            form.first_name.data = current_user.first_name or ''
            form.last_name.data = current_user.last_name or ''
            form.email.data = current_user.email or ''
            form.phone.data = current_user.phone or ''
            form.address.data = current_user.address or ''

    return render_template('checkout.html',
                           form=form,
                           cart_items=cart_items,
                           total=total,
                           cart_count=len(cart_items))


@main_bp.route('/account')
@login_required
def account():
    """Личный кабинет пользователя"""
    orders = current_user.orders.order_by(Order.created_at.desc()).all()
    return render_template('account.html', orders=orders)


@main_bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """Страница с деталями заказа"""
    order = Order.query.get_or_404(order_id)

    # Проверяем, что заказ принадлежит текущему пользователю
    if order.user_id != current_user.id:
        abort(403)

    return render_template('order_detail.html', order=order)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа в систему"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if request.method == 'POST':
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя пользователя или пароль', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember.data)

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')

        return redirect(next_page)
    return render_template('login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if request.method == 'POST':
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Поздравляем, вы успешно зарегистрировались!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth_bp.route('/logout')
def logout():
    """Выход из системы"""
    logout_user()
    return redirect(url_for('main.index'))


@auth_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Редактирование профиля пользователя"""
    form = EditProfileForm()

    if request.method == 'POST':
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data

        db.session.commit()
        flash('Ваши изменения сохранены.', 'success')
        return redirect(url_for('main.account'))

    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email.data = current_user.email
        form.phone.data = current_user.phone
        form.address.data = current_user.address

    return render_template('edit_profile.html', form=form)

@main_bp.route('/stats')
@login_required
def sales_stats():
    """Страница статистики продаж"""
    # Получаем данные из логов и cookies
    stats = {
        'visits': get_visit_stats(),
        'sales': get_sales_stats(),
        'popular_products': get_popular_products(),
        'conversion': get_conversion_rate()
    }
    return render_template('stats.html', stats=stats)