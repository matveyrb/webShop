from datetime import datetime, timedelta
from sqlalchemy import func, distinct
from app.models import VisitLog, SalesStat, Product, CartItem, Order, db


def get_visit_stats(days=30):
    """Статистика посещаемости за последние N дней"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Получаем данные посещений
    visits_data = (
        db.session.query(
            func.date(VisitLog.timestamp).label('date'),
            func.count().label('count')
        )
        .filter(VisitLog.timestamp >= cutoff_date)
        .group_by(func.date(VisitLog.timestamp))
        .order_by(func.date(VisitLog.timestamp))
        .all()
    )

    return {
        'total': sum(v.count for v in visits_data),
        'unique': db.session.query(func.count(distinct(VisitLog.ip_address)))
        .filter(VisitLog.timestamp >= cutoff_date)
        .scalar(),
        'days': [v.date.strftime('%d.%m') for v in visits_data],
        'visits_data': [v.count for v in visits_data]
    }


def get_sales_stats(days=30):
    """Статистика продаж за последние N дней"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    sales_data = (
        db.session.query(
            func.date(SalesStat.date).label('date'),
            func.sum(SalesStat.quantity).label('quantity'),
            func.sum(SalesStat.amount).label('amount')
        )
        .filter(SalesStat.date >= cutoff_date)
        .group_by(func.date(SalesStat.date))
        .order_by(func.date(SalesStat.date))
        .all()
    )

    return {
        'dates': [s.date.strftime('%d.%m') for s in sales_data],
        'quantities': [s.quantity or 0 for s in sales_data],
        'amounts': [s.amount or 0 for s in sales_data]
    }


def get_popular_products(limit=10):
    """Топ-N популярных товаров"""
    return (
        db.session.query(
            Product,
            func.sum(SalesStat.quantity).label('total_quantity'),
            func.sum(SalesStat.amount).label('total_amount')
        )
        .join(SalesStat)
        .group_by(Product.id)
        .order_by(db.desc('total_quantity'))
        .limit(limit)
        .all()
    )


def get_conversion_rate(days=30):
    """Расчет коэффициента конверсии"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    views = (
            db.session.query(func.count(VisitLog.id))
            .filter(VisitLog.timestamp >= cutoff_date)
            .filter(VisitLog.page_url.like('%product%'))
            .scalar() or 1  # Избегаем деления на 0
    )

    carts = (
        db.session.query(func.count(CartItem.id))
        .filter(CartItem.created_at >= cutoff_date)
        .scalar()
    )

    purchases = (
        db.session.query(func.count(Order.id))
        .filter(Order.created_at >= cutoff_date)
        .scalar()
    )

    return {
        'views': views,
        'add_to_cart': carts,
        'purchases': purchases,
        'rate': round((purchases / views) * 100, 2) if views else 0
    }