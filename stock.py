#!/usr/bin/env python3
"""
A股数据获取命令行工具 - 多功能版本
支持K线数据、实时行情、财务数据等多种功能
"""

import click
import baostock as bs
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box

from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from datetime import datetime, timedelta
import os


console = Console()

# 配置文件相关工具
def get_config_path(config_path=None):
    if config_path:
        return config_path
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stocks.txt')

def ensure_config_file(config_path):
    if not os.path.exists(config_path):
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(
                "sh.600000 # 浦发银行\n"
                "sz.000002 # 万科A\n"
                "sh.601398 # 工商银行\n"
            )

def read_stock_codes(config_path):
    stock_codes = []
    with open(config_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            code = line.split('#')[0].strip()
            if code:
                stock_codes.append(code)
    return stock_codes

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    🚀 A股数据获取工具 - 专业版股票数据分析CLI
    
    ═══════════════════════════════════════════════════════════════
    📊 功能概览
    ═══════════════════════════════════════════════════════════════
    
    • kline    - 📈 获取K线数据 (日线/周线/月线)
    • info     - ℹ️  获取股票基本信息 (公司信息、行业分类)
    • realtime - ⚡ 获取实时行情数据 (当前价格、涨跌)
    • finance  - 💰 获取财务数据 (利润表、资产负债表、现金流)
    • index    - 📊 查询指数成分股 (上证50、沪深300、中证500)
    • batch    - 📦 批量统计（配置文件驱动多股票K线统计）
    
    ═══════════════════════════════════════════════════════════════
    🎯 股票代码格式说明
    ═══════════════════════════════════════════════════════════════
    
    支持以下格式：
    • 完整格式: sz.000001 (深交所) / sh.600000 (上交所)
    • 简写格式: 000001 (0/3开头自动识别为深交所)
    •          600000 (6开头自动识别为上交所)
    
    ═══════════════════════════════════════════════════════════════
    💡 使用示例
    ═══════════════════════════════════════════════════════════════
    
    基础查询:
    python stock.py kline 000001              # 平安银行最近30天K线
    python stock.py info sz.000001            # 平安银行基本信息
    python stock.py finance 600000 -y 2023   # 浦发银行2023年财务数据

    高级查询:
    python stock.py kline 000001 -d 60 --export data.csv  # 60天数据并导出
    python stock.py kline 600000 -s 2023-01-01 -e 2023-12-31  # 指定日期范围
    python stock.py index -i hs300 --export hs300.csv         # 沪深300成分股

    批量查询:
    python stock.py realtime 000001 600000 000002    # 多只股票实时行情

    批量统计:
    python stock.py batch                # 默认读取 stocks.txt，统计30天
    python stock.py batch --days 60      # 统计最近60天
    python stock.py batch --config my_stocks.txt  # 指定配置文件
    
    ═══════════════════════════════════════════════════════════════
    🔗 附加功能
    ═══════════════════════════════════════════════════════════════
    
    • 🎨 Rich界面美化 - 彩色表格和图表显示
    • 📊 智能统计分析 - 自动计算涨跌分布、投资收益模拟
    • 💾 数据导出 - 支持CSV格式导出，便于Excel分析
    • 🔗 快速链接 - 自动生成百度股市通、东方财富、百度搜索链接
    • 📈 多维度数据 - K线、财务、行业、指数一站式查询
    
    ═══════════════════════════════════════════════════════════════
    ⚠️  注意事项
    ═══════════════════════════════════════════════════════════════
    
    • 数据来源: baostock (免费、稳定的A股数据接口)
    • 更新频率: 日线数据T+1更新，财务数据按季度更新
    • 网络要求: 需要稳定的网络连接获取实时数据
    • Python版本: 建议Python 3.7+
    
    ═══════════════════════════════════════════════════════════════
    🆘 获取帮助
    ═══════════════════════════════════════════════════════════════
    
    python stock.py [命令] --help     # 查看具体命令的详细帮助
    python stock.py --version         # 查看工具版本信息
    
    示例:
    python stock.py kline --help      # 查看K线命令的详细参数说明
    python stock.py finance --help    # 查看财务数据命令的参数说明
    """
    pass

@cli.command()
@click.argument('stock_code', type=str, required=True)
@click.option('--start', '-s', type=str, help='开始日期 (YYYY-MM-DD)', default=None)
@click.option('--end', '-e', type=str, help='结束日期 (YYYY-MM-DD)', default=None)
@click.option('--days', '-d', type=int, help='获取最近N天数据', default=30)
@click.option('--frequency', '-f', type=click.Choice(['5m', '15m', '30m', '60m', 'd', 'w', 'M']), 
              help='K线周期: 5m=5分钟, 15m=15分钟, 30m=30分钟, 60m=60分钟, d=日线, w=周线, M=月线', default='d')
@click.option('--export', type=click.Path(), help='导出到CSV文件')
def kline(stock_code, start, end, days, frequency, export):
    """
    📈 获取股票K线数据 - 多周期行情分析
    
    ══════════════════════════════════════════════════════════
    📊 功能说明
    ══════════════════════════════════════════════════════════
    
    获取指定股票的K线数据，支持多种时间周期：
    • 📈 OHLC数据: 开盘价、最高价、最低价、收盘价
    • 📊 成交数据: 成交量、成交额、换手率
    • 📉 涨跌数据: 涨跌幅、前收盘价
    • 🏷️  交易状态: 是否停牌、是否ST
    • 📈 智能分析: 涨跌分布统计、投资收益模拟
    • ⏱️  多周期: 支持分钟线、日线、周线、月线
    
    ══════════════════════════════════════════════════════════
    📝 参数说明
    ══════════════════════════════════════════════════════════
    
    STOCK_CODE: 股票代码 (必需)
      • 支持格式: sz.000001, sh.600000, 000001, 600000
      • 自动识别: 0/3开头→深交所, 6开头→上交所
    
    --start, -s: 开始日期 (可选)
      • 格式: YYYY-MM-DD (如: 2023-01-01)
      • 默认: 根据--days参数自动计算
    
    --end, -e: 结束日期 (可选)  
      • 格式: YYYY-MM-DD (如: 2023-12-31)
      • 默认: 当前日期
    
    --days, -d: 最近N天 (可选, 默认: 30)
      • 当未指定start/end时生效
      • 建议范围: 1-365天
    
    --frequency, -f: K线周期 (可选, 默认: d)
      • 分钟线: 5m=5分钟, 15m=15分钟, 30m=30分钟, 60m=60分钟
      • 日线: d=日线 (默认)
      • 周线: w=周线
      • 月线: M=月线
      • 注意: 分钟线数据仅支持最近几个月的数据
    
    --export: 导出文件路径 (可选)
      • 格式: CSV文件 (UTF-8编码)
      • 示例: --export /path/to/data.csv
    
    ══════════════════════════════════════════════════════════
    💡 使用示例
    ══════════════════════════════════════════════════════════
    
    基础查询:
      python stock.py kline 000001                    # 平安银行最近30天日线
      python stock.py kline sz.000001 -d 60          # 最近60天日线数据
      python stock.py kline 600000 -f w              # 浦发银行周线数据
    
    多周期查询:
      python stock.py kline 000001 -f 5m             # 5分钟K线
      python stock.py kline 000001 -f 15m            # 15分钟K线  
      python stock.py kline 000001 -f 30m            # 30分钟K线
      python stock.py kline 000001 -f 60m            # 60分钟K线
      python stock.py kline 000001 -f d              # 日线（默认）
      python stock.py kline 000001 -f w              # 周线
      python stock.py kline 000001 -f M              # 月线
    
    日期范围查询:
      python stock.py kline 000001 -s 2023-01-01 -e 2023-12-31  # 2023年全年日线
      python stock.py kline 000001 -f w -s 2023-01-01           # 2023年以来周线
      python stock.py kline 000001 -f 5m -d 3                   # 最近3天5分钟线
    
    数据导出:
      python stock.py kline 000001 --export data.csv           # 导出日线到CSV
      python stock.py kline 000001 -f w --export weekly.csv   # 导出周线数据
    
    ══════════════════════════════════════════════════════════
    📊 输出说明
    ══════════════════════════════════════════════════════════
    
    • 📈 K线表格: 日期、OHLC、涨跌幅、成交量/额
    • 📊 统计面板: 交易统计、涨跌分布、价格变化、成交统计
    • 💰 投资模拟: 基于1万元本金的收益模拟算
    • 🔗 快速链接: 百度股市通、东方财富、百度搜索
    
    ══════════════════════════════════════════════════════════
    ⚠️  注意事项
    ══════════════════════════════════════════════════════════
    
    • 数据更新: T+1更新 (当日数据次日可查)
    • 节假日: 非交易日无数据返回
    • 停牌股票: 停牌期间数据可能不完整
    • 网络连接: 需要稳定网络连接baostock服务器
    """
    # 验证和格式化股票代码
    if not stock_code or not stock_code.strip():
        console.print("[red]❌ 错误: 请提供股票代码[/red]")
        console.print("\n[yellow]💡 使用示例:[/yellow]")
        console.print("  python stock_cli_multi.py kline sz.000001    # 深交所股票")
        console.print("  python stock_cli_multi.py kline sh.600000    # 上交所股票")
        return
    
    stock_code = format_stock_code(stock_code.strip())
    if not stock_code:
        return
    
    # 如果没有指定开始和结束日期，使用days参数
    if not start and not end:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start = start_date.strftime('%Y-%m-%d')
        end = end_date.strftime('%Y-%m-%d')
    elif not start:
        start = (datetime.strptime(end, '%Y-%m-%d') - timedelta(days=days)).strftime('%Y-%m-%d')
    elif not end:
        end = datetime.now().strftime('%Y-%m-%d')
    
    # 频率映射和描述
    frequency_map = {
        '5m': ('5', '5分钟'),
        '15m': ('15', '15分钟'), 
        '30m': ('30', '30分钟'),
        '60m': ('60', '60分钟'),
        'd': ('d', '日线'),
        'w': ('w', '周线'),
        'M': ('M', '月线')
    }
    
    bao_frequency, freq_desc = frequency_map[frequency]
    console.print(f"[blue]📈 正在获取 {stock_code} 从 {start} 到 {end} 的{freq_desc}数据...[/blue]")
    
    # 登录baostock系统
    lg = bs.login()
    if lg.error_code != '0':
        console.print(f"[red]baostock登录失败: {lg.error_msg}[/red]")
        return
    
    try:
        # 根据频率选择不同的查询方法和字段
        if frequency in ['5m', '15m', '30m', '60m']:
            # 分钟线数据查询
            rs = bs.query_history_k_data_plus(
                stock_code,
                "date,time,code,open,high,low,close,volume,amount,adjustflag",
                start_date=start,
                end_date=end,
                frequency=bao_frequency,
                adjustflag="3"
            )
        elif frequency in ['w', 'M']:
            # 周线/月线数据查询（字段限制）
            rs = bs.query_history_k_data_plus(
                stock_code,
                "date,code,open,high,low,close,volume,amount,adjustflag",
                start_date=start,
                end_date=end,
                frequency=bao_frequency,
                adjustflag="3"
            )
        else:
            # 日线数据查询
            rs = bs.query_history_k_data_plus(
                stock_code,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
                start_date=start,
                end_date=end,
                frequency=bao_frequency,
                adjustflag="3"
            )
        
        if rs.error_code != '0':
            console.print(f"[red]数据获取失败: {rs.error_msg}[/red]")
            return
        
        # 将数据转换为DataFrame
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            console.print(f"[yellow]未找到 {stock_code} 在指定日期范围内的数据[/yellow]")
            return
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        # 根据频率类型进行不同的数据处理
        if frequency in ['5m', '15m', '30m', '60m']:
            # 分钟线数据类型转换
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'amount']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            # 合并日期时间列
            if 'time' in df.columns:
                df['datetime'] = df['date'] + ' ' + df['time']
        elif frequency in ['w', 'M']:
            # 周线/月线数据类型转换
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'amount']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            # 日线数据类型转换
            numeric_columns = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn', 'pctChg']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 创建Rich表格
        table = Table(
            title=f"📈 {stock_code} {freq_desc}数据 ({start} ~ {end})",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            row_styles=["", "on grey11"],
            padding=(1, 1)
        )
        
        # 根据频率类型添加不同的列
        if frequency in ['5m', '15m', '30m', '60m']:
            # 分钟线表格列
            table.add_column("日期时间", style="cyan", justify="center")
            table.add_column("开盘", style="white", justify="right")
            table.add_column("最高", style="white", justify="right")
            table.add_column("最低", style="white", justify="right")
            table.add_column("收盘", style="white", justify="right")
            table.add_column("成交量", style="blue", justify="right")
            table.add_column("成交额", style="blue", justify="right")
        elif frequency in ['w', 'M']:
            # 周线/月线表格列（不显示涨跌幅）
            table.add_column("日期", style="cyan", justify="center")
            table.add_column("开盘", style="white", justify="right")
            table.add_column("最高", style="white", justify="right")
            table.add_column("最低", style="white", justify="right")
            table.add_column("收盘", style="white", justify="right")
            table.add_column("成交量", style="blue", justify="right")
            table.add_column("成交额", style="blue", justify="right")
        else:
            # 日线表格列
            table.add_column("日期", style="cyan", justify="center")
            table.add_column("开盘", style="white", justify="right")
            table.add_column("最高", style="white", justify="right")
            table.add_column("最低", style="white", justify="right")
            table.add_column("收盘", style="white", justify="right")
            table.add_column("涨跌幅", style="white", justify="right")
            table.add_column("成交量", style="blue", justify="right")
            table.add_column("成交额", style="blue", justify="right")
        
        # 添加数据行
        for _, row in df.iterrows():
            # 格式化成交量和成交额
            volume = int(row['volume']) if pd.notna(row['volume']) else 0
            amount = float(row['amount']) if pd.notna(row['amount']) else 0
            volume_str = f"{volume:,}" if volume > 0 else "-"
            amount_str = f"{amount/100000000:.2f}亿" if amount > 100000000 else f"{amount/10000:.2f}万" if amount > 10000 else f"{amount:.0f}"

            if frequency in ['5m', '15m', '30m', '60m']:
                table.add_row(
                    row['datetime'] if 'datetime' in row else row['date'],
                    f"{float(row['open']):.2f}" if pd.notna(row['open']) else "-",
                    f"{float(row['high']):.2f}" if pd.notna(row['high']) else "-",
                    f"{float(row['low']):.2f}" if pd.notna(row['low']) else "-",
                    f"{float(row['close']):.2f}" if pd.notna(row['close']) else "-",
                    volume_str,
                    amount_str
                )
            elif frequency in ['w', 'M']:
                table.add_row(
                    row['date'],
                    f"{float(row['open']):.2f}" if pd.notna(row['open']) else "-",
                    f"{float(row['high']):.2f}" if pd.notna(row['high']) else "-",
                    f"{float(row['low']):.2f}" if pd.notna(row['low']) else "-",
                    f"{float(row['close']):.2f}" if pd.notna(row['close']) else "-",
                    volume_str,
                    amount_str
                )
            else:
                pct_change = float(row['pctChg']) if pd.notna(row['pctChg']) else 0
                pct_style = "red" if pct_change > 0 else "green" if pct_change < 0 else "white"
                pct_text = f"{pct_change:+.2f}%" if pct_change != 0 else "0.00%"
                table.add_row(
                    row['date'],
                    f"{float(row['open']):.2f}" if pd.notna(row['open']) else "-",
                    f"{float(row['high']):.2f}" if pd.notna(row['high']) else "-",
                    f"{float(row['low']):.2f}" if pd.notna(row['low']) else "-",
                    f"{float(row['close']):.2f}" if pd.notna(row['close']) else "-",
                    f"[{pct_style}]{pct_text}[/{pct_style}]",
                    volume_str,
                    amount_str
                )
        
        console.print(table)
        
        # 显示统计信息 (简化版)
        display_kline_stats(df, frequency)
        
        # 导出数据
        if export:
            df.to_csv(export, index=False, encoding='utf-8-sig')
            console.print(f"\n[green]✅ 数据已导出到: {export}[/green]")
        
        # 显示股票链接
        display_stock_link(stock_code)
    
    finally:
        # 登出baostock系统
        bs.logout()
    
@cli.command()
@click.argument('stock_code', type=str, required=True)
def info(stock_code):
    """
    ℹ️  获取股票基本信息 - 公司档案查询
    
    ══════════════════════════════════════════════════════════
    📋 功能说明  
    ══════════════════════════════════════════════════════════
    
    查询指定股票的基本信息，包括：
    • 🏢 公司信息: 股票代码、股票名称
    • 📅 重要日期: 上市日期、退市日期
    • 🏷️  股票属性: 股票类型、交易状态
    • 🏭 行业信息: 所属行业、行业分类
    
    ══════════════════════════════════════════════════════════
    📝 参数说明
    ══════════════════════════════════════════════════════════
    
    STOCK_CODE: 股票代码 (必需)
      • 支持格式: sz.000001, sh.600000, 000001, 600000  
      • 自动识别: 0/3开头→深交所, 6开头→上交所
    
    ══════════════════════════════════════════════════════════
    💡 使用示例
    ══════════════════════════════════════════════════════════
    
    基础查询:
      python stock.py info 000001          # 平安银行基本信息
      python stock.py info sz.000001       # 同上 (完整格式)
      python stock.py info 600000          # 浦发银行基本信息
      python stock.py info sh.600000       # 同上 (完整格式)
    
    批量查询建议:
      python stock.py info 000001 && python stock.py info 600000  # 依次查询
    
    ══════════════════════════════════════════════════════════
    📊 输出说明
    ══════════════════════════════════════════════════════════
    
    • 📋 基本信息表: 代码、名称、上市日期、股票类型、交易状态
    • 🏢 行业信息表: 所属行业、行业分类详情
    • 🔗 快速链接: 百度股市通、东方财富、百度搜索链接
    
    ══════════════════════════════════════════════════════════
    🔍 股票类型说明
    ══════════════════════════════════════════════════════════
    
    • 股票: 普通A股
    • B股: 外资股 (以美元或港币计价)
    • 存托凭证: CDR等特殊证券
    
    ══════════════════════════════════════════════════════════
    ⚠️  注意事项  
    ══════════════════════════════════════════════════════════
    
    • 数据来源: baostock基础数据库
    • 行业分类: 按照证监会行业分类标准
    • 退市股票: 显示退市日期，基本信息可能不完整
    • 新股上市: 上市首日后1-2个工作日可查询到信息
    """
    stock_code = format_stock_code(stock_code.strip())
    if not stock_code:
        return
    
    console.print(f"[blue]📋 正在获取 {stock_code} 的基本信息...[/blue]")
    
    # 登录baostock
    lg = bs.login()
    if lg.error_code != '0':
        console.print(f"[red]baostock登录失败: {lg.error_msg}[/red]")
        return
    
    try:
        # 获取股票基本信息
        rs = bs.query_stock_basic(code=stock_code)
        if rs.error_code != '0':
            console.print(f"[red]获取股票信息失败: {rs.error_msg}[/red]")
            return
            
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        if data_list:
            info_data = dict(zip(rs.fields, data_list[0]))
            
            # 创建信息表格
            table = Table(title=f"📋 {stock_code} 基本信息", box=box.ROUNDED, padding=(1, 1))
            table.add_column("项目", style="cyan", width=12)
            table.add_column("内容", style="white")
            
            table.add_row("股票代码", info_data.get('code', '-'))
            table.add_row("股票名称", info_data.get('code_name', '-'))
            table.add_row("上市日期", info_data.get('ipoDate', '-'))
            table.add_row("退市日期", info_data.get('outDate', '-') or '[green]正常交易[/green]')
            table.add_row("股票类型", get_stock_type_desc(info_data.get('type', '-')))
            table.add_row("交易状态", get_status_desc(info_data.get('status', '-')))
            
            console.print(table)
            
            # 获取行业信息
            get_industry_info(stock_code)
            
            # 显示股票链接
            display_stock_link(stock_code)
            
        else:
            console.print(f"[yellow]未找到 {stock_code} 的基本信息[/yellow]")
            
    finally:
        bs.logout()

def get_stock_type_desc(type_code):
    """获取股票类型描述"""
    type_map = {
        '1': '股票',
        '2': 'B股',
        '3': '存托凭证'
    }
    return type_map.get(type_code, type_code or '-')

def get_status_desc(status_code):
    """获取交易状态描述"""
    status_map = {
        '1': '[green]正常交易[/green]',
        '0': '[red]停牌[/red]'
    }
    return status_map.get(status_code, status_code or '-')

def get_industry_info(stock_code):
    """获取行业信息"""
    try:
        rs = bs.query_stock_industry(code=stock_code)
        if rs.error_code == '0':
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if data_list:
                industry_data = dict(zip(rs.fields, data_list[0]))
                
                # 创建行业信息表格
                table = Table(title=f"🏢 行业信息", box=box.ROUNDED, padding=(1, 1))
                table.add_column("项目", style="cyan", width=12)
                table.add_column("内容", style="white")
                
                table.add_row("所属行业", industry_data.get('industry', '-'))
                table.add_row("行业分类", industry_data.get('industryClassification', '-'))
                
                console.print("\n")
                console.print(table)
    except Exception as e:
        # 行业信息获取失败不影响主要功能
        pass

@cli.command()
@click.argument('stock_codes', nargs=-1, required=True)
def realtime(stock_codes):
    """
    ⚡ 获取实时行情数据 - 多股票实时监控
    
    ══════════════════════════════════════════════════════════
    📊 功能说明
    ══════════════════════════════════════════════════════════
    
    获取指定股票的实时行情数据，支持：
    • 📈 实时价格: 当前最新成交价格
    • 📊 涨跌信息: 涨跌额、涨跌幅、涨跌状态
    • 🔄 批量查询: 同时监控多只股票行情
    • ⚡ 快速响应: 实时更新的市场数据
    
    ══════════════════════════════════════════════════════════
    📝 参数说明
    ══════════════════════════════════════════════════════════
    
    STOCK_CODES: 股票代码列表 (支持多个)
      • 支持格式: sz.000001, sh.600000, 000001, 600000
      • 自动识别: 0/3开头→深交所, 6开头→上交所
      • 批量查询: 空格分隔多个股票代码
      • 数量限制: 建议单次查询不超过20只股票
    
    ══════════════════════════════════════════════════════════
    💡 使用示例
    ══════════════════════════════════════════════════════════
    
    单股票查询:
      python stock.py realtime 000001              # 平安银行实时行情
      python stock.py realtime sz.000001           # 同上 (完整格式)
      python stock.py realtime 600000              # 浦发银行实时行情
    
    多股票批量查询:
      python stock.py realtime 000001 600000       # 两只银行股
      python stock.py realtime 000001 600000 000002 # 三只股票
      python stock.py realtime sz.000001 sh.600000 sz.000002  # 完整格式
    
    行业监控示例:
      python stock.py realtime 600036 601318 000858  # 银行股监控
      python stock.py realtime 000002 000069 001979  # 地产股监控  
      python stock.py realtime 600519 000568 002304  # 消费股监控
    
    指数成分股监控:
      # 先查询指数成分股，再选择重点股票监控
      python stock.py index -i sz50 --export sz50.csv
      python stock.py realtime 600519 000001 600036  # 监控权重股
    
    ══════════════════════════════════════════════════════════
    📊 输出说明
    ══════════════════════════════════════════════════════════
    
    • 📋 实时行情表: 股票代码、名称、现价、涨跌额、涨跌幅
    • 🎨 颜色标识: 红色上涨、绿色下跌、白色平盘
    • ⚡ 实时状态: 显示数据获取时间和市场状态
    • 📊 排序显示: 按涨跌幅排序，便于快速识别强势股
    
    ══════════════════════════════════════════════════════════
    ⏰ 交易时间说明
    ══════════════════════════════════════════════════════════
    
    A股交易时间:
      • 上午: 09:30-11:30 (开盘集合竞价: 09:15-09:25)
      • 下午: 13:00-15:00 (收盘集合竞价: 14:57-15:00)
      • 休市: 周末、法定节假日
    
    数据更新频率:
      • 交易时间: 实时更新 (延迟约3-5秒)
      • 非交易时间: 显示上一交易日收盘数据
      • 停牌股票: 显示停牌前最后成交价格
    
    ══════════════════════════════════════════════════════════
    📈 使用技巧
    ══════════════════════════════════════════════════════════
    
    • 🔄 定时监控: 结合系统定时任务实现自动监控
      crontab -e  # 添加: */5 * * * * python /path/to/stock.py realtime 000001
    
    • 📊 组合监控: 配合指数查询构建投资组合监控
      python stock.py index -i hs300 | grep "000001\\|600000" # 筛选关注股票
    
    • 🚨 预警设置: 结合脚本实现价格预警 (需自行开发)
    • 📱 移动监控: 在手机终端中使用 (需安装Python环境)
    
    ══════════════════════════════════════════════════════════
    ⚠️  注意事项
    ══════════════════════════════════════════════════════════
    
    • 🚧 功能状态: 当前为演示版本，显示模拟数据
    • 🔌 数据源: 需要接入实时行情数据接口 (如新浪、腾讯等)
    • 💰 费用说明: 实时数据可能需要付费订阅
    • 📊 延迟说明: 免费数据通常有3-15分钟延迟
    • 🏷️  免责声明: 数据仅供参考，投资决策请谨慎
    • 🔒 使用限制: 请遵守数据提供商的使用条款
    """
    console.print(f"[blue]获取实时行情数据...[/blue]")
    
    # 创建实时行情表格
    table = Table(title="⚡ 实时行情", box=box.ROUNDED)
    table.add_column("股票代码", style="cyan")
    table.add_column("股票名称", style="white")
    table.add_column("现价", style="white")
    table.add_column("涨跌", style="white")
    table.add_column("涨跌幅", style="white")
    
    for code in stock_codes:
        formatted_code = format_stock_code(code)
        if formatted_code:
            # 这里可以添加实时数据获取逻辑
            table.add_row(formatted_code, "示例股票", "10.00", "+0.50", "+5.26%")
    
    console.print(table)
    console.print("[yellow]注: 实时数据功能需要接入实时数据源[/yellow]")

@cli.command()
@click.argument('stock_code', type=str, required=True)
@click.option('--year', '-y', type=str, help='查询年份 (YYYY)', default=None)
@click.option('--quarter', '-q', type=int, help='查询季度 (1-4)', default=None)
def finance(stock_code, year, quarter):
    """
    💰 获取财务数据 - 三大报表分析
    
    ══════════════════════════════════════════════════════════
    📊 功能说明
    ══════════════════════════════════════════════════════════
    
    获取指定股票的季度财务报表数据，包括：
    • 📊 利润表: 营收、成本、利润、每股收益等
    • 🏦 资产负债表: 总资产、负债、股东权益等  
    • 💰 现金流量表: 经营、投资、筹资现金流等
    • 📈 智能分析: 自动计算关键财务比率
    
    ══════════════════════════════════════════════════════════
    📝 参数说明
    ══════════════════════════════════════════════════════════
    
    STOCK_CODE: 股票代码 (必需)
      • 支持格式: sz.000001, sh.600000, 000001, 600000
      • 自动识别: 0/3开头→深交所, 6开头→上交所
    
    --year, -y: 查询年份 (可选)
      • 格式: YYYY (如: 2023)
      • 默认: 上一年 (当年数据可能未发布)
      • 范围: 2007年至今
    
    --quarter, -q: 查询季度 (可选)
      • 范围: 1-4 (1=Q1, 2=Q2, 3=Q3, 4=Q4年报)
      • 默认: 4 (年报数据最完整)
      • 建议: Q4年报数据最准确完整
    
    ══════════════════════════════════════════════════════════
    💡 使用示例
    ══════════════════════════════════════════════════════════
    
    基础查询:
      python stock.py finance 000001               # 平安银行上年年报
      python stock.py finance sz.000001            # 同上 (完整格式)
      python stock.py finance 600000               # 浦发银行上年年报
    
    指定年份查询:
      python stock.py finance 000001 -y 2023      # 2023年年报
      python stock.py finance 000001 -y 2022      # 2022年年报
      python stock.py finance 000001 -y 2023 -q 3 # 2023年三季报
    
    季度报告查询:
      python stock.py finance 000001 -q 1         # 上年一季报
      python stock.py finance 000001 -q 2         # 上年中报  
      python stock.py finance 000001 -q 3         # 上年三季报
      python stock.py finance 000001 -q 4         # 上年年报
    
    历史数据查询:
      python stock.py finance 000001 -y 2020 -q 4 # 2020年年报
      python stock.py finance 000001 -y 2019 -q 4 # 2019年年报
    
    ══════════════════════════════════════════════════════════
    📊 输出说明
    ══════════════════════════════════════════════════════════
    
    📊 利润表 (经营成果):
      • 营业收入、营业成本、营业利润
      • 利润总额、净利润、每股收益
    
    🏦 资产负债表 (财务状况):
      • 总资产、总负债、股东权益
      • 流动资产、流动负债
    
    💰 现金流量表 (现金状况):
      • 经营活动现金流、投资活动现金流
      • 筹资活动现金流、现金净增加额
    
    🔗 快速链接:
      • 百度股市通、东方财富、百度搜索
    
    ══════════════════════════════════════════════════════════
    📅 财报时间说明
    ══════════════════════════════════════════════════════════
    
    • Q1 一季报: 1-3月数据, 4月底前发布
    • Q2 中期报告: 1-6月数据, 8月底前发布  
    • Q3 三季报: 1-9月数据, 10月底前发布
    • Q4 年度报告: 全年数据, 次年4月底前发布
    
    ══════════════════════════════════════════════════════════
    ⚠️  注意事项
    ══════════════════════════════════════════════════════════
    
    • 数据更新: 按季度更新，存在1-3个月延迟
    • 年报推荐: Q4年报数据最完整准确
    • 数据缺失: 部分小公司或ST公司数据可能不完整
    • 单位说明: 金额自动转换为万元/亿元显示
    • 历史数据: 支持查询2007年以来的财务数据
    """
    stock_code = format_stock_code(stock_code.strip())
    if not stock_code:
        return
    
    # 设置默认查询时间
    if not year:
        year = str(datetime.now().year - 1)  # 默认查询去年数据，因为当年数据可能还未发布
    if not quarter:
        quarter = 4
    
    console.print(f"[blue]💰 正在获取 {stock_code} 的财务数据 ({year}Q{quarter})...[/blue]")
    
    # 登录baostock
    lg = bs.login()
    if lg.error_code != '0':
        console.print(f"[red]baostock登录失败: {lg.error_msg}[/red]")
        return
    
    try:
        # 获取季度利润表数据
        rs_profit = bs.query_profit_data(code=stock_code, year=year, quarter=quarter)
        
        # 获取季度现金流量表数据
        rs_cash = bs.query_cash_flow_data(code=stock_code, year=year, quarter=quarter)
        
        # 获取季度资产负债表数据
        rs_balance = bs.query_balance_data(code=stock_code, year=year, quarter=quarter)
        
        # 处理利润表数据
        profit_data = {}
        if rs_profit.error_code == '0':
            while (rs_profit.error_code == '0') & rs_profit.next():
                row_data = rs_profit.get_row_data()
                profit_data = dict(zip(rs_profit.fields, row_data))
                break
        
        # 处理现金流数据
        cash_data = {}
        if rs_cash.error_code == '0':
            while (rs_cash.error_code == '0') & rs_cash.next():
                row_data = rs_cash.get_row_data()
                cash_data = dict(zip(rs_cash.fields, row_data))
                break
        
        # 处理资产负债表数据
        balance_data = {}
        if rs_balance.error_code == '0':
            while (rs_balance.error_code == '0') & rs_balance.next():
                row_data = rs_balance.get_row_data()
                balance_data = dict(zip(rs_balance.fields, row_data))
                break
        
        if not any([profit_data, cash_data, balance_data]):
            console.print(f"[yellow]未找到 {stock_code} 在 {year}Q{quarter} 的财务数据[/yellow]")
            console.print("[dim]提示: 尝试查询其他年份或季度[/dim]")
            return
        
        # 创建财务数据表格
        display_finance_data(stock_code, year, quarter, profit_data, cash_data, balance_data)
        
        # 显示股票链接
        display_stock_link(stock_code)
        
    finally:
        bs.logout()

def display_finance_data(stock_code, year, quarter, profit_data, cash_data, balance_data):
    """显示财务数据"""
    
    def format_amount(value_str):
        """格式化金额显示"""
        try:
            if not value_str or value_str == '' or value_str == 'None':
                return '-'
            value = float(value_str)
            if abs(value) >= 100000000:  # 亿
                return f"{value/100000000:.2f}亿"
            elif abs(value) >= 10000:  # 万
                return f"{value/10000:.2f}万"
            else:
                return f"{value:.0f}"
        except:
            return value_str or '-'
    
    # 利润表数据
    if profit_data:
        table1 = Table(title=f"📊 利润表 ({year}Q{quarter})", box=box.ROUNDED, padding=(1, 1))
        table1.add_column("财务指标", style="cyan", width=15)
        table1.add_column("金额", style="white", justify="right")
        
        table1.add_row("营业收入", format_amount(profit_data.get('totalOperatingRevenue', '')))
        table1.add_row("营业成本", format_amount(profit_data.get('operatingCost', '')))
        table1.add_row("营业利润", format_amount(profit_data.get('operatingProfit', '')))
        table1.add_row("利润总额", format_amount(profit_data.get('totalProfit', '')))
        table1.add_row("净利润", format_amount(profit_data.get('netProfit', '')))
        table1.add_row("每股收益", format_amount(profit_data.get('basicEarningsPerShare', '')))
        
        console.print(table1)
    
    # 资产负债表数据
    if balance_data:
        table2 = Table(title=f"🏦 资产负债表 ({year}Q{quarter})", box=box.ROUNDED, padding=(1, 1))
        table2.add_column("财务指标", style="cyan", width=15)
        table2.add_column("金额", style="white", justify="right")
        
        table2.add_row("总资产", format_amount(balance_data.get('totalAssets', '')))
        table2.add_row("总负债", format_amount(balance_data.get('totalLiabilities', '')))
        table2.add_row("股东权益", format_amount(balance_data.get('totalShareholderEquity', '')))
        table2.add_row("流动资产", format_amount(balance_data.get('totalCurrentAssets', '')))
        table2.add_row("流动负债", format_amount(balance_data.get('totalCurrentLiabilities', '')))
        
        console.print("\n")
        console.print(table2)
    
    # 现金流量表数据
    if cash_data:
        table3 = Table(title=f"💰 现金流量表 ({year}Q{quarter})", box=box.ROUNDED, padding=(1, 1))
        table3.add_column("财务指标", style="cyan", width=15)
        table3.add_column("金额", style="white", justify="right")
        
        table3.add_row("经营现金流", format_amount(cash_data.get('operatingCashFlow', '')))
        table3.add_row("投资现金流", format_amount(cash_data.get('investingCashFlow', '')))
        table3.add_row("筹资现金流", format_amount(cash_data.get('financingCashFlow', '')))
        table3.add_row("现金净增加", format_amount(cash_data.get('netIncreaseInCash', '')))
        
        console.print("\n")
        console.print(table3)

def format_stock_code(stock_code):
    """格式化股票代码"""
    if not stock_code or not stock_code.strip():
        console.print("[red]❌ 错误: 股票代码不能为空[/red]")
        return None
    
    stock_code = stock_code.strip()
    
    if not stock_code.startswith(('sz.', 'sh.')):
        if stock_code.startswith('0') or stock_code.startswith('3'):
            stock_code = f'sz.{stock_code}'
        elif stock_code.startswith('6'):
            stock_code = f'sh.{stock_code}'
        else:
            console.print(f"[red]❌ 错误: 无法识别股票代码格式: {stock_code}[/red]")
            console.print("\n[yellow]💡 支持的格式:[/yellow]")
            console.print("  • sz.000001 (深交所完整格式)")
            console.print("  • sh.600000 (上交所完整格式)")
            console.print("  • 000001   (深交所简写，0或3开头)")
            console.print("  • 600000   (上交所简写，6开头)")
            return None
    
    return stock_code

def display_kline_stats(df, frequency='d'):
    """显示K线统计信息"""
    total_days = len(df)
    
    # 检查是否存在 pctChg 字段，如果不存在，则计算涨跌幅
    if 'pctChg' not in df.columns:
        # 对于周线/月线数据，需要手动计算涨跌幅
        df['pctChg'] = df['close'].astype(float).pct_change() * 100
        # 第一行的涨跌幅无法计算，设为0
        df['pctChg'] = df['pctChg'].fillna(0)
    
    up_days = len(df[df['pctChg'].astype(float) > 0])
    down_days = len(df[df['pctChg'].astype(float) < 0])
    flat_days = total_days - up_days - down_days
    
    # 计算价格统计
    prices = df['close'].astype(float)
    price_change = prices.iloc[-1] - prices.iloc[0] if len(prices) > 1 else 0
    price_change_pct = (price_change / prices.iloc[0] * 100) if len(prices) > 1 and prices.iloc[0] != 0 else 0
    
    # 根据频率设置交易周期描述
    period_desc = {
        'd': '交易日',
        'w': '交易周',
        'M': '交易月'
    }.get(frequency, '交易日')
    
    # 对于分钟级别的K线，计算实际的交易天数
    if frequency in ['5m', '15m', '30m', '60m']:
        # 提取日期部分（不含时间）
        if 'date' in df.columns:
            unique_days = df['date'].nunique()
            trading_days_text = f"总交易日: {unique_days} 天 ({total_days} 个{frequency}周期)"
        else:
            trading_days_text = f"总交易日: {total_days} 个{frequency}周期"
    else:
        # 对于日线、周线、月线
        trading_days_text = f"总{period_desc}: {total_days}"
        if frequency == 'd':
            trading_days_text += " 天"
        elif frequency == 'w':
            trading_days_text += " 周"
        elif frequency == 'M':
            trading_days_text += " 月"
    
    # 交易日统计
    trading_stats = Text()
    trading_stats.append("📊 ", style="bold blue")
    trading_stats.append("交易统计", style="bold white")
    trading_stats.append(f"\n{trading_days_text}", style="white")
    
    # 涨跌统计
    trend_stats = Text()
    trend_stats.append("📈 ", style="bold red")
    trend_stats.append("涨跌分布", style="bold white")
    trend_stats.append(f"\n上涨: ", style="white")
    trend_stats.append(f"{up_days}", style="bold red")
    trend_stats.append(f" ({up_days/total_days*100:.1f}%)", style="red")
    trend_stats.append(f"\n下跌: ", style="white")
    trend_stats.append(f"{down_days}", style="bold green")
    trend_stats.append(f" ({down_days/total_days*100:.1f}%)", style="green")
    if flat_days > 0:
        trend_stats.append(f"\n平盘: ", style="white")
        trend_stats.append(f"{flat_days}", style="bold yellow")
        trend_stats.append(f" ({flat_days/total_days*100:.1f}%)", style="yellow")
    
    # 价格变化统计
    price_stats = Text()
    price_stats.append("💰 ", style="bold yellow")
    price_stats.append("价格变化", style="bold white")
    if len(prices) > 1:
        price_color = "red" if price_change > 0 else "green" if price_change < 0 else "white"
        price_stats.append(f"\n期间涨跌: ", style="white")
        price_stats.append(f"{price_change:+.2f}", style=f"bold {price_color}")
        price_stats.append(f" ({price_change_pct:+.2f}%)", style=price_color)
        price_stats.append(f"\n起始价格: ", style="white")
        price_stats.append(f"{prices.iloc[0]:.2f}", style="cyan")
        price_stats.append(f"\n结束价格: ", style="white")
        price_stats.append(f"{prices.iloc[-1]:.2f}", style="cyan")
    
    # 成交量统计
    volumes = df['volume'].astype(float)
    avg_volume = volumes.mean() if len(volumes) > 0 else 0
    max_volume = volumes.max() if len(volumes) > 0 else 0
        
    volume_stats = Text()
    volume_stats.append("📊 ", style="bold magenta")
    volume_stats.append("成交统计", style="bold white")
    volume_stats.append(f"\n平均成交量: ", style="white")
    volume_stats.append(f"{int(avg_volume):,}", style="bold blue")
    volume_stats.append(f"\n最大成交量: ", style="white")
    volume_stats.append(f"{int(max_volume):,}", style="bold blue")

    # 投资收益模拟
    investment_amount = 10000  # 假设投资1万元
    if len(prices) > 1 and prices.iloc[0] != 0:
        shares_bought = investment_amount / prices.iloc[0]  # 能买多少股
        final_value = shares_bought * prices.iloc[-1]  # 最终价值
        profit_loss = final_value - investment_amount  # 盈亏
        profit_loss_pct = (profit_loss / investment_amount) * 100  # 盈亏百分比
    else:
        shares_bought = 0
        final_value = investment_amount
        profit_loss = 0
        profit_loss_pct = 0
        
    investment_stats = Text()
    investment_stats.append("💰 ", style="bold cyan")
    investment_stats.append("投资模拟", style="bold white")
    investment_stats.append(f"\n投入本金: ", style="white")
    investment_stats.append(f"¥{investment_amount:,.0f}", style="bold cyan")
    if len(prices) > 1:
        investment_stats.append(f"\n购买股数: ", style="white")
        investment_stats.append(f"{shares_bought:.0f}", style="cyan")
        investment_stats.append("股", style="white")
        investment_stats.append(f"\n最终价值: ", style="white")
        investment_stats.append(f"¥{final_value:,.2f}", style="bold cyan")
            
        profit_color = "red" if profit_loss > 0 else "green" if profit_loss < 0 else "white"
        profit_symbol = "📈" if profit_loss > 0 else "📉" if profit_loss < 0 else "➖"
        investment_stats.append(f"\n{profit_symbol} ", style=profit_color)
        if profit_loss > 0:
            investment_stats.append("盈利: ", style="white")
            investment_stats.append(f"+¥{profit_loss:,.2f}", style=f"bold {profit_color}")
        elif profit_loss < 0:
            investment_stats.append("亏损: ", style="white")
            investment_stats.append(f"¥{profit_loss:,.2f}", style=f"bold {profit_color}")
        else:
            investment_stats.append("持平", style="white")
        investment_stats.append(f" ({profit_loss_pct:+.2f}%)", style=profit_color)

    # 创建列布局 - 分两行显示
    top_panels = [
        Panel(trading_stats, title="📈", border_style="blue", padding=(0, 1)),
        Panel(trend_stats, title="📊", border_style="red", padding=(0, 1)),
        Panel(price_stats, title="💰", border_style="yellow", padding=(0, 1))
    ]
        
    bottom_panels = [
        Panel(investment_stats, title="💰", border_style="cyan", padding=(0, 1)),
        Panel(volume_stats, title="📊", border_style="magenta", padding=(0, 1))
    ]
        
    console.print("\n")
    console.print(Columns(top_panels, equal=False, expand=False, align="left"))
    console.print(Columns(bottom_panels, equal=False, expand=False, align="left"))

@cli.command()
@click.option('--index', '-i', type=click.Choice(['sz50', 'hs300', 'zz500']), required=True, help='指数类型')
@click.option('--export', type=click.Path(), help='导出到CSV文件')
def index(index, export):
    """
    📊 查询指数成分股 - 主流指数成分分析
    
    ══════════════════════════════════════════════════════════
    📈 功能说明
    ══════════════════════════════════════════════════════════
    
    查询主流A股指数的成分股列表，包括：
    • 📋 成分股清单: 完整的股票代码和名称列表
    • 📊 统计分析: 成分股数量、交易所分布统计
    • 📅 更新信息: 最新的成分股调整日期
    • 💾 数据导出: 支持导出为CSV格式便于分析
    
    ══════════════════════════════════════════════════════════
    📝 参数说明
    ══════════════════════════════════════════════════════════
    
    --index, -i: 指数类型 (必需)
      • sz50   - 上证50指数成分股
      • hs300  - 沪深300指数成分股
      • zz500  - 中证500指数成分股
    
    --export: 导出文件路径 (可选)
      • 格式: CSV文件 (UTF-8编码)
      • 包含: 股票代码、名称、更新日期
      • 示例: --export /path/to/index_stocks.csv
    
    ══════════════════════════════════════════════════════════
    📊 指数介绍
    ══════════════════════════════════════════════════════════
    
    📈 上证50 (sz50):
      • 指数代码: sh.000016
      • 成分股数: 50只
      • 选股范围: 上交所规模大、流动性好的50只股票
      • 代表性: 大盘蓝筹股，金融、地产权重较高
    
    📊 沪深300 (hs300):
      • 指数代码: sh.000300  
      • 成分股数: 300只
      • 选股范围: 沪深两市规模最大的300只股票
      • 代表性: A股市场整体表现的核心指标
    
    📉 中证500 (zz500):
      • 指数代码: sh.000905
      • 成分股数: 500只  
      • 选股范围: 除沪深300外规模排名前500的股票
      • 代表性: 中小盘股票，成长性较强
    
    ══════════════════════════════════════════════════════════
    💡 使用示例
    ══════════════════════════════════════════════════════════
    
    基础查询:
      python stock.py index -i sz50        # 上证50成分股
      python stock.py index -i hs300       # 沪深300成分股
      python stock.py index -i zz500       # 中证500成分股
    
    数据导出:
      python stock.py index -i sz50 --export sz50_stocks.csv     # 导出上证50
      python stock.py index -i hs300 --export hs300_stocks.csv   # 导出沪深300
      python stock.py index -i zz500 --export zz500_stocks.csv   # 导出中证500
    
    组合分析建议:
      python stock.py index -i hs300 --export hs300.csv && \\
      python stock.py kline 000001 --export 000001.csv          # 先导出指数再分析个股
    
    ══════════════════════════════════════════════════════════
    📊 输出说明
    ══════════════════════════════════════════════════════════
    
    • 📋 成分股表格: 序号、股票代码、股票名称、更新日期
    • 📊 指数信息面板: 指数名称、代码、成分股总数
    • 🏢 交易所分布: 上交所和深交所的成分股数量分布
    • 📅 数据时效: 显示最新的成分股调整日期
    
    ══════════════════════════════════════════════════════════
    📅 成分股调整说明
    ══════════════════════════════════════════════════════════
    
    • 调整频率: 
      - 上证50: 每年6月、12月调整
      - 沪深300: 每年6月、12月调整  
      - 中证500: 每年6月、12月调整
    
    • 调整原则: 按市值、流动性、财务状况等指标筛选
    • 生效时间: 调整后的下个交易日生效
    • 历史数据: 显示当前最新的成分股构成
    
    ══════════════════════════════════════════════════════════
    ⚠️  注意事项
    ══════════════════════════════════════════════════════════
    
    • 数据实时性: 成分股调整后1-2个工作日更新
    • 停牌股票: 停牌股票仍在成分股列表中显示
    • 退市股票: 退市股票会被及时从指数中剔除
    • 投资参考: 成分股列表可作为投资组合参考
    • 权重信息: 当前版本不包含权重数据，仅提供成分股列表
    """
    
    # 指数代码映射
    index_codes = {
        'sz50': 'sh.000016',    # 上证50
        'hs300': 'sh.000300',   # 沪深300
        'zz500': 'sh.000905'    # 中证500
    }
    
    index_names = {
        'sz50': '上证50',
        'hs300': '沪深300', 
        'zz500': '中证500'
    }
    
    console.print(f"[blue]📊 正在获取 {index_names[index]} 成分股数据...[/blue]")
    
    # 登录baostock系统
    lg = bs.login()
    if lg.error_code != '0':
        console.print(f"[red]baostock登录失败: {lg.error_msg}[/red]")
        return
    
    try:
        # 获取指数成分股
        if index == 'sz50':
            rs = bs.query_sz50_stocks(date=datetime.now().strftime('%Y-%m-%d'))
        elif index == 'hs300':
            rs = bs.query_hs300_stocks(date=datetime.now().strftime('%Y-%m-%d'))
        elif index == 'zz500':
            rs = bs.query_zz500_stocks(date=datetime.now().strftime('%Y-%m-%d'))
        
        if rs.error_code != '0':
            console.print(f"[red]成分股数据获取失败: {rs.error_msg}[/red]")
            return
        
        # 将数据转换为DataFrame
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            console.print(f"[yellow]未找到 {index_names[index]} 的成分股数据[/yellow]")
            return
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        # 创建Rich表格
        table = Table(
            title=f"📊 {index_names[index]} 成分股列表 (共{len(df)}只)",
            box=box.ROUNDED,
            expand=True,
            show_header=True,
            header_style="bold magenta",
            row_styles=["", "on grey11"],
            padding=(1, 1),
        )
        
        # 添加列
        table.add_column("序号", style="cyan", justify="center", width=6)
        table.add_column("股票代码", style="yellow", justify="center", width=12)
        table.add_column("股票名称", style="white", justify="left", width=15)
        table.add_column("更新日期", style="blue", justify="center", width=12)
        
        # 添加数据行
        for idx, (_, row) in enumerate(df.iterrows(), 1):
            table.add_row(
                str(idx),
                row['code'],
                row['code_name'] if 'code_name' in row else '-',
                row['updateDate'] if 'updateDate' in row else '-'
            )
        
        console.print(table)
        
        # 显示统计信息
        display_index_stats(index_names[index], index_codes[index], df)
        
        # 导出数据
        if export:
            df.to_csv(export, index=False, encoding='utf-8-sig')
            console.print(f"\n[green]✅ 数据已导出到: {export}[/green]")
    
    finally:
        # 登出baostock系统
        bs.logout()

def display_index_stats(index_name, index_code, df):
    """显示指数统计信息"""
    stats_text = Text()
    stats_text.append("📈 ", style="bold blue")
    stats_text.append("指数信息", style="bold white")
    stats_text.append(f"\n指数名称: ", style="white")
    stats_text.append(f"{index_name}", style="bold cyan")
    stats_text.append(f"\n指数代码: ", style="white")
    stats_text.append(f"{index_code}", style="bold yellow")
    stats_text.append(f"\n成分股数: ", style="white")
    stats_text.append(f"{len(df)}", style="bold green")
    stats_text.append(" 只", style="white")
    
    # 统计交易所分布
    sz_count = len([code for code in df['code'] if code.startswith('sz.')])
    sh_count = len([code for code in df['code'] if code.startswith('sh.')])
    
    distribution_text = Text()
    distribution_text.append("🏢 ", style="bold green")
    distribution_text.append("交易所分布", style="bold white")
    distribution_text.append(f"\n上交所: ", style="white")
    distribution_text.append(f"{sh_count}", style="bold red")
    distribution_text.append(" 只", style="white")
    distribution_text.append(f"\n深交所: ", style="white")
    distribution_text.append(f"{sz_count}", style="bold blue")
    distribution_text.append(" 只", style="white")
    
    panels = [
        Panel(stats_text, title="📊", border_style="blue", padding=(0, 1)),
        Panel(distribution_text, title="🏢", border_style="green", padding=(0, 1))
    ]
    
    console.print("\n")
    console.print(Columns(panels, equal=True, expand=False, align="left"))

def display_stock_link(stock_code):
    """显示股票链接"""
    # 提取纯股票代码（去掉sz.或sh.前缀）
    clean_code = stock_code.replace('sz.', '').replace('sh.', '')
    
    # 生成完整股票代码（保留交易所前缀，转换为大写）
    full_code = stock_code.upper().replace('.', '')  # sz.000001 -> SZ000001
    
    # 百度股市通链接
    baidu_link = f"https://gushitong.baidu.com/stock/ab-{clean_code}"
    
    # 东方财富链接
    eastmoney_link = f"https://quote.eastmoney.com/concept/{full_code}.html?from=data"
    
    # 百度搜索链接
    baidu_search_link = f"https://www.baidu.com/s?wd={clean_code}"
    
    # 创建可点击的链接
    link_text = Text()
    link_text.append("🔗 ", style="bold blue")
    link_text.append("百度股市通: ", style="white")
    link_text.append(baidu_link, style="bold cyan underline")
    link_text.append("\n📈 ", style="bold green")
    link_text.append("东方财富 : ", style="white")
    link_text.append(eastmoney_link, style="bold green underline")
    link_text.append("\n🔍 ", style="bold yellow")
    link_text.append("百度搜索 : ", style="white")
    link_text.append(baidu_search_link, style="bold yellow underline")
    
    panel = Panel(link_text, title="📊 查看更多", border_style="cyan", padding=(0, 1),width=100)
    console.print("\n")
    console.print(panel)


@cli.command()
@click.option('--config', type=click.Path(), help='配置文件路径（默认为程序同目录下的 stocks.txt）')
@click.option('--days', '-d', type=int, help='获取最近N天数据', default=30)
def batch(config, days):
    """
    📦 批量统计命令 - 配置文件驱动的多股票K线统计

    ══════════════════════════════════════════════════════════
    📊 功能说明
    ══════════════════════════════════════════════════════════
    读取配置文件中的股票代码，循环输出每只股票的K线统计信息（仅统计结果，不显示明细表格）。
    支持自动创建配置文件并写入示例内容。

    ══════════════════════════════════════════════════════════
    📝 参数说明
    ══════════════════════════════════════════════════════════
    --config: 配置文件路径（可选）
        • 默认读取程序同目录下的 stocks.txt
        • 如不存在会自动创建并写入示例内容

    --days, -d: 最近N天（可选，默认30）
        • 统计每只股票最近N天的K线数据

    ══════════════════════════════════════════════════════════
    💡 使用示例
    ══════════════════════════════════════════════════════════
    python stock.py batch                # 默认读取 stocks.txt，统计30天
    python stock.py batch --days 60      # 统计最近60天
    python stock.py batch --config my_stocks.txt  # 指定配置文件

    ══════════════════════════════════════════════════════════
    📄 配置文件格式说明
    ══════════════════════════════════════════════════════════
    stocks.txt 示例：
        sh.600000 # 浦发银行
        sz.000002 # 万科A
        sh.601398 # 工商银行
    每行“股票代码 + 空格 + # + 注释”，注释可选。

    ══════════════════════════════════════════════════════════
    📊 输出说明
    ══════════════════════════════════════════════════════════
    • 仅输出每只股票的统计信息（涨跌分布、价格变化、投资模拟等）
    • 不显示明细K线表格
    """
    config_path = get_config_path(config)
    ensure_config_file(config_path)
    codes = read_stock_codes(config_path)
    if not codes:
        console.print(f"[red]配置文件 {config_path} 中没有有效的股票代码[/red]")
        return
    console.print(f"[blue]批量统计，读取配置文件: {config_path}[/blue]")
    for code in codes:
        stock_code = format_stock_code(code)
        if not stock_code:
            continue
        # 获取最近N天K线数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start = start_date.strftime('%Y-%m-%d')
        end = end_date.strftime('%Y-%m-%d')
        lg = bs.login()
        if lg.error_code != '0':
            console.print(f"[red]baostock登录失败: {lg.error_msg}[/red]")
            continue
        try:
            rs = bs.query_history_k_data_plus(
                stock_code,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
                start_date=start,
                end_date=end,
                frequency="d",
                adjustflag="3"
            )
            if rs.error_code != '0':
                console.print(f"[red]{stock_code} 数据获取失败: {rs.error_msg}[/red]")
                continue
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            if not data_list:
                console.print(f"[yellow]未找到 {stock_code} 在指定日期范围内的数据[/yellow]")
                continue
            df = pd.DataFrame(data_list, columns=rs.fields)
            numeric_columns = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn', 'pctChg']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            # 只输出统计信息
            console.print(f"\n[bold green]统计: {stock_code}[/bold green]")
            display_kline_stats(df)
        finally:
            bs.logout()

if __name__ == '__main__':
    cli()
