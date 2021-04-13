import datetime
import json

import numpy as np
import pandas as pd

from customer.models import Customer
from dashboard.constant import StatisticType
from order.constant import OrderStatus
from order.models import Order, OrderDetail
from product.models import Product


def list_shop_dashboard_data(
    shop_id: int,
    from_date: datetime.date,
    to_date: datetime.date,
    statistic_type: int,
):
    """
    获取店铺经营数据
    :param shop_id:
    :param from_date:
    :param to_date:
    :param statistic_type: 统计数据类型 1:日 3:月 4:年
    :return:
    """
    if statistic_type == StatisticType.DAILY:
        fmt = "%Y-%m-%d"
    elif statistic_type == StatisticType.MONTHLY:
        fmt = "%Y-%m"
    else:
        fmt = "%Y"
    # 订单
    orders = (
        Order.objects.filter(
            shop_id=shop_id,
            create_date__range=[from_date, to_date],
            order_status__in=[
                    OrderStatus.PAID,
                    OrderStatus.CONFIRMED,
                    OrderStatus.FINISHED,
                    OrderStatus.REFUNDED,
                ]
        )
        .all()
    )
    orders = list(orders.values("create_date", "order_status", "total_amount_net"))
    orders_frame = pd.DataFrame(
        orders, columns=["create_date", "status", "total_amount_net"]
    )
    orders_agg_valid = (
        orders_frame.loc[orders_frame.status != OrderStatus.REFUNDED]
            .groupby(orders_frame["create_date"].apply(lambda x: x.strftime(fmt)))
            .agg(
            order_amount_valid=pd.NamedAgg(column="total_amount_net", aggfunc=sum),
            order_count_valid=pd.NamedAgg(column="status", aggfunc=len),
        )
    )
    orders_agg_all = orders_frame.groupby(
        orders_frame["create_date"].apply(lambda x: x.strftime(fmt))
    ).agg(order_count_all=pd.NamedAgg(column="status", aggfunc=len))
    orders_agg = pd.merge(
        orders_agg_all, orders_agg_valid, how="left", on="create_date"
    ).fillna(0)
    # 客户
    customers = (
        Customer.objects.filter(
            shop_id=shop_id,
            create_date__range=[from_date, to_date],
        )
        .all()
    )
    customers = list(customers.values("create_date", "id"))
    customers_frame = pd.DataFrame(customers, columns=["create_date", "id"])
    customers_agg = customers_frame.groupby(
        customers_frame["create_date"].apply(lambda x: x.strftime(fmt))
    ).agg(customer_new_count=pd.NamedAgg(column="id", aggfunc=len))

    shop_agg = pd.merge(orders_agg, customers_agg, how="outer", on="create_date")
    if shop_agg.empty:
        return True, []

    shop_agg["amount_per_order"] = shop_agg.apply(
        lambda x: float(x["order_amount_valid"]) / x["order_count_valid"]
        if x["order_count_valid"] > 0
        else 0,
        axis=1,
    )
    shop_agg.fillna(0, inplace=True)
    shop_agg.sort_index(ascending=False, inplace=True)
    # 类型转换及圆整 .map(lambda x: ('%.2f') %x)
    shop_agg["order_count_all"] = shop_agg["order_count_all"].astype("int")
    shop_agg["order_amount_valid"] = (
        shop_agg["order_amount_valid"].astype("float").round(decimals=2)
    )
    shop_agg["order_count_valid"] = shop_agg["order_count_valid"].astype("int")
    shop_agg["customer_new_count"] = shop_agg["customer_new_count"].astype("int")
    shop_agg["amount_per_order"] = (
        shop_agg["amount_per_order"].astype("float").round(decimals=2)
    )
    return True, json.loads(shop_agg.to_json(orient="table"))["data"]


def list_order_dashboard_data(
    shop_id: int,
    from_date: datetime.date,
    to_date: datetime.date,
    statistic_type: int,
):
    """
    获取订单数据
    :param shop_id:
    :param from_date:
    :param to_date:
    :param statistic_type:
    :return:
    """
    if statistic_type == StatisticType.DAILY:
        fmt = "%Y-%m-%d"
    elif statistic_type == StatisticType.MONTHLY:
        fmt = "%Y-%m"
    else:
        fmt = "%Y"
    # 订单
    orders = (
        Order.objects.filter(
            shop_id=shop_id,
            create_date__range=[from_date, to_date],
            order_status__in=[
                OrderStatus.PAID,
                OrderStatus.CONFIRMED,
                OrderStatus.FINISHED,
                OrderStatus.REFUNDED,
            ]
        )
            .all()
    )
    orders = list(orders.values("create_date", "order_status", "total_amount_net"))
    orders_frame = pd.DataFrame(
        orders, columns=["create_date", "status", "total_amount_net"]
    )
    orders_agg_valid = (
        orders_frame.loc[orders_frame.status != OrderStatus.REFUNDED]
            .groupby(orders_frame["create_date"].apply(lambda x: x.strftime(fmt)))
            .agg(
            order_amount_valid=pd.NamedAgg(column="total_amount_net", aggfunc="sum"),
            order_count_valid=pd.NamedAgg(column="status", aggfunc="count"),
        )
    )
    orders_agg_all = orders_frame.groupby(
        orders_frame["create_date"].apply(lambda x: x.strftime(fmt))
    ).agg(
        order_amount_all=pd.NamedAgg(column="total_amount_net", aggfunc="sum"),
        order_count_all=pd.NamedAgg(column="status", aggfunc="count"),
    )
    orders_agg = pd.merge(
        orders_agg_all, orders_agg_valid, how="left", on="create_date"
    ).fillna(0)
    if orders_agg.empty:
        return True, []

    orders_agg["order_amount_refund"] = orders_agg.apply(
        lambda x: float(x["order_amount_all"]) - float(x["order_amount_valid"]), axis=1
    )
    orders_agg["order_count_refund"] = orders_agg.apply(
        lambda x: float(x["order_count_all"]) - float(x["order_count_valid"]), axis=1
    )
    orders_agg.fillna(0, inplace=True)
    orders_agg.sort_index(ascending=False, inplace=True)
    # 类型转换及圆整 .map(lambda x: ('%.2f') %x)
    orders_agg["order_count_all"] = orders_agg["order_count_all"].astype("int")
    orders_agg["order_count_valid"] = orders_agg["order_count_valid"].astype("int")
    orders_agg["order_count_refund"] = orders_agg["order_count_refund"].astype("int")
    orders_agg["order_amount_all"] = (
        orders_agg["order_amount_all"].astype("float").round(decimals=2)
    )
    orders_agg["order_amount_valid"] = (
        orders_agg["order_amount_valid"].astype("float").round(decimals=2)
    )
    orders_agg["order_amount_refund"] = (
        orders_agg["order_amount_refund"].astype("float").round(decimals=2)
    )

    return True, json.loads(orders_agg.to_json(orient="table"))["data"]


def list_product_dashboard_data(
    shop_id: int, from_date: datetime.date, to_date: datetime.date
):
    """
    获取订单数据
    :param shop_id:
    :param from_date:
    :param to_date:
    :return:
    """
    product_details = (
        OrderDetail.objects.filter(
            shop_id=shop_id,
            create_date__range=[from_date, to_date],
        )
        .all()
    )
    product_details = list(product_details.values(
        "amount_net",
        "quantity_net",
        "product_id",
        "customer_id",
        "status",
    ))
    products_frame = pd.DataFrame(
        product_details,
        columns=[
            "order_amount_net",
            "order_quantity_net",
            "product_id",
            "customer_id",
            "status",
        ],
    )
    orders_agg_all = products_frame.groupby("product_id").agg(
        order_count=pd.NamedAgg(column="status", aggfunc="count")
    )
    if orders_agg_all.empty:
        return True, []
    orders_agg_paid = (
        products_frame.loc[
            (products_frame["status"] >= OrderStatus.PAID)
            & (products_frame["status"] < OrderStatus.REFUNDED)
            ]
            .groupby("product_id")
            .agg(
            order_count_paid=pd.NamedAgg(column="status", aggfunc="count"),
            order_amount_paid=pd.NamedAgg(column="order_amount_net", aggfunc="sum"),
            order_quantity_net=pd.NamedAgg(column="order_quantity_net", aggfunc="sum"),
        )
    )
    products_agg = pd.merge(
        orders_agg_all, orders_agg_paid, how="left", on="product_id"
    ).fillna(0)

    # 复购率分析
    customer_pivot = (
        products_frame.loc[products_frame["status"] >= OrderStatus.PAID]
            .pivot_table(
            index="customer_id", columns="product_id", values="status", aggfunc="count"
        )
            .applymap(lambda x: 1 if x > 1 else 0 if x == 1 else np.NaN)
    )
    customers_agg = customer_pivot.sum() / customer_pivot.count()
    if customers_agg.empty:
        products_agg["rebuy_rate"] = [0 for i in range(products_agg.index.size)]
    else:
        products_agg["rebuy_rate"] = customers_agg

    # 拼商品名
    product_ids = [l["product_id"] for l in product_details]
    products = (
        Product.objects.filter(
            id__in=product_ids
        )
        .all()
    )
    products = list(products.values(
        "id",
        "name",
        "group_id",
        "group__name",
    ))
    products_info_frame = pd.DataFrame(
        products,
        columns=[
            "product_id",
            "product_name",
            "product_group_id",
            "product_group_name",
        ],
    )
    products_agg = pd.merge(products_agg, products_info_frame, on="product_id")
    products_agg.fillna(0, inplace=True)
    products_agg["order_amount_paid"] = (
        products_agg["order_amount_paid"].astype("float").round(decimals=2)
    )
    products_agg["rebuy_rate"] = (
        products_agg["rebuy_rate"].astype("float").round(decimals=2)
    )
    products_agg["order_quantity_net"] = (
        products_agg["order_quantity_net"].astype("float").round(decimals=2)
    )

    return True, products_agg.to_dict(orient="records")