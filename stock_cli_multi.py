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

console = Console()

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    🚀 A股数据获取工具
    
    支持多种数据查询功能：
    • kline - 获取K线数据
    • info - 获取股票基本信息  
    • realtime - 获取实时行情
    • finance - 获取财务数据
    • index - 查询指数成分股
    """
    pass

@cli.command()
@click.argument('stock_code', type=str, required=True)
@click.option('--start', '-s', type=str, help='开始日期 (YYYY-MM-DD)', default=None)
@click.option('--end', '-e', type=str, help='结束日期 (YYYY-MM-DD)', default=None)
@click.option('--days', '-d', type=int, help='获取最近N天数据', default=30)
@click.option('--export', type=click.Path(), help='导出到CSV文件')
def kline(stock_code, start, end, days, export):
    """
    📈 获取股票K线数据
    
    STOCK_CODE: 股票代码 (如: sz.000001 或 sh.600000)
    
    示例:
      stock_cli_multi.py kline sz.000001
      stock_cli_multi.py kline 600000 -d 60
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
    
    console.print(f"[blue]📈 正在获取 {stock_code} 从 {start} 到 {end} 的日K线数据...[/blue]")
    
    # 登录baostock系统
    lg = bs.login()
    if lg.error_code != '0':
        console.print(f"[red]baostock登录失败: {lg.error_msg}[/red]")
        return
    
    try:
        # 获取日K线数据
        rs = bs.query_history_k_data_plus(
            stock_code,
            "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
            start_date=start,
            end_date=end,
            frequency="d",
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
        
        # 数据类型转换
        numeric_columns = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn', 'pctChg']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 创建Rich表格
        table = Table(
            title=f"📈 {stock_code} 日K线数据 ({start} ~ {end})",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            row_styles=["", "on grey11"],
            padding=(1, 1)
        )
        
        # 添加列
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
            pct_change = float(row['pctChg']) if pd.notna(row['pctChg']) else 0
            pct_style = "red" if pct_change > 0 else "green" if pct_change < 0 else "white"
            pct_text = f"{pct_change:+.2f}%" if pct_change != 0 else "0.00%"
            
            # 格式化成交量和成交额
            volume = int(row['volume']) if pd.notna(row['volume']) else 0
            amount = float(row['amount']) if pd.notna(row['amount']) else 0
            
            volume_str = f"{volume:,}" if volume > 0 else "-"
            amount_str = f"{amount/100000000:.2f}亿" if amount > 100000000 else f"{amount/10000:.2f}万" if amount > 10000 else f"{amount:.0f}"
            
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
        display_kline_stats(df)
        
        # 导出数据
        if export:
            df.to_csv(export, index=False, encoding='utf-8-sig')
            console.print(f"\n[green]✅ 数据已导出到: {export}[/green]")
    
    finally:
        # 登出baostock系统
        bs.logout()
    
@cli.command()
@click.argument('stock_code', type=str, required=True)
def info(stock_code):
    """
    ℹ️  获取股票基本信息
    
    包括公司名称、行业、上市日期等信息
    
    示例:
      stock_cli_multi.py info sz.000001
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
    ⚡ 获取实时行情数据
    
    可以同时查询多个股票的实时数据
    
    示例:
      stock_cli_multi.py realtime sz.000001
      stock_cli_multi.py realtime sz.000001 sh.600000 sz.000002
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
    💰 获取财务数据
    
    获取股票的季度财务报表数据
    
    示例:
      stock_cli_multi.py finance sz.000001
      stock_cli_multi.py finance sz.000001 -y 2023 -q 4
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
                return f"{value:.2f}"
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

def display_kline_stats(df):
    """显示K线统计信息"""
    total_days = len(df)
    up_days = len(df[df['pctChg'].astype(float) > 0])
    down_days = len(df[df['pctChg'].astype(float) < 0])
    flat_days = total_days - up_days - down_days
    
    # 计算价格统计
    prices = df['close'].astype(float)
    price_change = prices.iloc[-1] - prices.iloc[0] if len(prices) > 1 else 0
    price_change_pct = (price_change / prices.iloc[0] * 100) if len(prices) > 1 and prices.iloc[0] != 0 else 0
    
    # 交易日统计
    trading_stats = Text()
    trading_stats.append("📊 ", style="bold blue")
    trading_stats.append("交易统计", style="bold white")
    trading_stats.append(f"\n总交易日: ", style="white")
    trading_stats.append(f"{total_days}", style="bold cyan")
    trading_stats.append(" 天", style="white")
    
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
    📊 查询指数成分股
    
    指数类型:
      sz50   - 上证50成分股
      hs300  - 沪深300成分股  
      zz500  - 中证500成分股
    
    示例:
      stock_cli_multi.py index -i sz50       # 查询上证50成分股
      stock_cli_multi.py index -i hs300      # 查询沪深300成分股
      stock_cli_multi.py index -i zz500      # 查询中证500成分股
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

if __name__ == '__main__':
    cli()