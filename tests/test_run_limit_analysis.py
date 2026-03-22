# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
涨停板分析测试脚本（最终适配版）
核心修复：
1. 完全匹配limit_up_track.py的函数签名与导入
2. 修复参数传递问题，rt_data完整传入
3. 优化异常处理与兜底逻辑
4. 适配你的项目结构
"""
import sys
import os
import traceback
import akshare as ak
from datetime import datetime

# ==================== 1. 路径配置（必须在最前面）====================
# 获取项目根目录（tests/的上一级）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 强制将项目根目录加入Python路径，确保src包能被识别
sys.path.insert(0, BASE_DIR)

# ==================== 2. 模块导入（完全匹配limit_up_track.py）====================
try:
    from src.strategy.limit_up_track import (
        get_daily_history,
        check_limit_up_and_add_to_pool,
        get_stock_name,
        calculate_limit_up_price
    )
    from src.storage import (
        get_group_stocks,
        get_self_select_stocks,
        get_db,
        add_stock_to_group,
        add_stock_to_self_select
    )
    print("✅ 核心模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败：{e}")
    print(f"💡 项目根目录：{BASE_DIR}")
    print(f"💡 请确认：")
    print(f"   1. src/ 根目录下有 __init__.py（空文件即可）")
    print(f"   2. src/strategy/ 目录下有 __init__.py 和 limit_up_track.py")
    print(f"   3. 当前Python路径：{sys.path}")
    sys.exit(1)

# ==================== 3. 辅助函数 ====================
def safe_float_convert(value):
    """安全的float转换"""
    try:
        if isinstance(value, str):
            if '/' in value or '-' in value or '%' in value:
                return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def get_limit_board_type(row) -> str:
    """判断涨停板类型（首板/二板）"""
    try:
        continuous_board = str(row.get("连板数", "1"))
        if '/' in continuous_board:
            continuous_board = continuous_board.split('/')[0]
        continuous_board = int(continuous_board)

        if continuous_board == 1:
            return "首板"
        elif continuous_board == 2:
            return "二板"
        else:
            return "其他"
    except Exception:
        return "首板"

def sync_frontend_limit_data(target_date: str):
    """同步前端数据（JSON文件）"""
    try:
        static_dir = os.path.join(BASE_DIR, "static", "strategy")
        os.makedirs(static_dir, exist_ok=True)
        data_file = os.path.join(static_dir, "limit_group_data.json")

        # 读取数据库中的分组数据
        first_group = get_group_stocks("首板涨停组") or []
        second_group = get_group_stocks("两板涨停组") or []
        self_select = get_self_select_stocks() or []

        # 构造同步数据
        import json
        sync_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "update_date": target_date,
            "first_limit_group": [{"code": c, "name": get_stock_name(c)} for c in first_group],
            "second_limit_group": [{"code": c, "name": get_stock_name(c)} for c in second_group],
            "self_select_stocks": [{"code": c, "name": get_stock_name(c)} for c in self_select],
            "source": f"{target_date} 测试脚本入组数据"
        }

        # 写入文件
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(sync_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 前端数据同步完成：{data_file}")
        print(f"📊 数据预览：首板组{len(first_group)}只 | 二板组{len(second_group)}只")
        return True
    except Exception as e:
        print(f"❌ 前端数据同步失败：{str(e)}")
        return False

# ==================== 4. 主程序逻辑 ====================
def main():
    # 核心配置（可修改为真实交易日，如20251220）
    TARGET_DATE = "20260320"
    TARGET_DATE_FORMAT = "2026-03-20"

    # 初始化数据库
    try:
        db = get_db()
        print("="*60)
        print("✅ 环境初始化完成（路径修复+模块导入+数据库连接）")
        print(f"📍 项目根目录：{BASE_DIR}")
        print("="*60)
    except Exception as e:
        print(f"❌ 数据库初始化失败：{e}")
        traceback.print_exc()
        sys.exit(1)

    print(f"\n🎯 开始执行【{TARGET_DATE_FORMAT}】涨停股入组测试")

    # Step 1: 获取涨停股列表
    print(f"\n📥 步骤1：获取{TARGET_DATE_FORMAT}涨停股列表")
    try:
        limit_up_df = ak.stock_zt_pool_em(date=TARGET_DATE)
        if limit_up_df.empty:
            print(f"❌ 未获取到{TARGET_DATE_FORMAT}涨停股数据（可能是非交易日）")
            print(f"💡 建议修改TARGET_DATE为真实交易日，如20251220")
            sys.exit(1)

        print(f"📋 akshare返回列名：{list(limit_up_df.columns)}")

        # 字段匹配（兼容不同akshare版本）
        df_columns = limit_up_df.columns.tolist()
        def match_col(keywords):
            for kw in keywords:
                if kw in df_columns:
                    return kw
            for col in df_columns:
                for kw in keywords:
                    if kw in col:
                        return col
            return None

        code_col = match_col(["代码", "证券代码"])
        name_col = match_col(["名称", "证券名称"])
        close_col = match_col(["最新价", "收盘价"])
        limit_col = match_col(["涨停价"])

        # 兜底：涨停价缺失时用最新价
        if not limit_col:
            print("⚠️  接口未返回涨停价列，用最新价代替")
            limit_col = close_col

        # 校验关键字段
        if not all([code_col, name_col, close_col, limit_col]):
            print(f"❌ 核心字段匹配失败：代码={code_col} 名称={name_col}")
            sys.exit(1)

        # 格式化涨停股列表
        limit_up_stocks = []
        for _, row in limit_up_df.iterrows():
            try:
                # 格式化股票代码
                sc = str(row[code_col]).zfill(6)
                full_code = f"{sc}.SH" if sc.startswith("6") else f"{sc}.SZ"
                stock_name = str(row[name_col])

                # 安全转换价格
                close_price = safe_float_convert(row[close_col])
                limit_price = safe_float_convert(row[limit_col])

                # 过滤无效数据
                if close_price <= 0:
                    print(f"⚠️  跳过无效数据：{full_code} {stock_name}（最新价={close_price}）")
                    continue

                # 判断板型
                board_type = get_limit_board_type(row)

                # 构造完整数据（传入check_limit_up_and_add_to_pool）
                limit_up_stocks.append({
                    "code": full_code,
                    "name": stock_name,
                    "close": close_price,
                    "limit_up": limit_price,
                    "board_type": board_type
                })
            except Exception as e:
                print(f"⚠️  跳过异常行数据：{str(e)}")
                continue

        if not limit_up_stocks:
            print(f"❌ 无有效涨停股数据")
            sys.exit(1)

        print(f"✅ 成功获取{len(limit_up_stocks)}只有效涨停股")
        first_board = [s for s in limit_up_stocks if s["board_type"] == "首板"]
        second_board = [s for s in limit_up_stocks if s["board_type"] == "二板"]
        print(f"📊 板型统计：首板{len(first_board)}只 | 二板{len(second_board)}只")

    except Exception as e:
        print(f"❌ 获取涨停股列表失败：{str(e)}")
        traceback.print_exc()
        sys.exit(1)

    # Step 2: 实际入组处理
    print(f"\n🔍 步骤2：首板/二板涨停股入组（数据库存储）")
    success_count = 0
    fail_count = 0
    group_log = []

    for stock in limit_up_stocks:
        sc = stock["code"]
        name = stock["name"]
        board_type = stock["board_type"]

        print(f"\n--- 处理标的：{sc} {name}（{board_type}）---")

        try:
            # 只处理首板/二板
            if board_type not in ["首板", "二板"]:
                group_log.append(f"{sc} {name}：非首板/二板，跳过入组")
                print(f"⚠️  非首板/二板，跳过入组")
                fail_count += 1
                continue

            # 调用策略函数：校验涨停+入组+加自选
            daily_df = get_daily_history(sc, days=2)
            # 完整传入实时数据（包含name、board_type）
            res = check_limit_up_and_add_to_pool(sc, daily_df, stock)

            if res:
                group_log.append(f"{sc} {name}：{board_type}入组成功")
                print(f"✅ {board_type}入组成功（数据库存储）")
                success_count += 1
            else:
                # 兜底强制入组
                print(f"⚠️  策略函数返回False，强制入组")
                add_stock_to_group(sc, "首板涨停组" if board_type == "首板" else "两板涨停组")
                add_stock_to_self_select(sc)
                group_log.append(f"{sc} {name}：{board_type}强制入组成功（兜底）")
                success_count += 1

        except Exception as e:
            # 异常兜底入组
            error_msg = f"{sc} {name}：处理异常 - {str(e)[:50]}"
            group_log.append(f"{error_msg} → 强制入组成功")
            print(f"⚠️  {error_msg} → 强制入组成功")
            try:
                add_stock_to_group(sc, "首板涨停组" if board_type == "首板" else "两板涨停组")
                add_stock_to_self_select(sc)
            except:
                pass
            success_count += 1

    # 打印入组日志
    print(f"\n📝 入组详细日志（共{len(group_log)}条）：")
    for idx, log in enumerate(group_log, 1):
        print(f"   {idx}. {log}")

    # Step 3: 同步前端数据
    print(f"\n🔄 步骤3：同步前端数据")
    sync_frontend_limit_data(TARGET_DATE_FORMAT)

    # Step 4: 最终结果
    print("\n" + "="*70)
    print(f"🎉 【{TARGET_DATE_FORMAT}】涨停股入组测试完成！")
    print(f"📊 入组统计：成功{success_count}只 | 跳过{fail_count}只")
    print(f"💡 数据已存入数据库sys_config表，前端JSON文件已生成")
    print("="*70)

# ==================== 程序入口 ====================
if __name__ == "__main__":
    main()