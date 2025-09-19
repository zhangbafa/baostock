# CODEBUDDY.md

## 项目概述

这是一个基于 baostock 数据源的专业A股数据获取命令行工具，提供K线数据、实时行情、财务数据、指数成分股等多种功能。工具采用 Rich 库美化界面，支持彩色表格显示和数据导出。

## 开发环境设置

### 依赖安装
```bash
pip install -r requirements.txt
```

主要依赖：
- `baostock>=0.8.9` - A股数据接口
- `click>=8.0.0` - 命令行界面框架  
- `pandas>=1.3.0` - 数据处理
- `rich>=13.0.0` - 终端界面美化

### 运行主程序
```bash
python stock.py --help          # 查看总体帮助
python stock.py [命令] --help    # 查看具体命令帮助
python stock.py --version       # 查看版本信息
```

## 核心架构

### 主要文件结构
- `stock.py` - 主要的CLI工具，包含所有股票数据查询功能
- `pyweb.py` - 简单的Web界面演示（使用pywebview）
- `stock copy.py` - stock.py的备份版本
- `test.py` - 测试文件
- `index.html` - Web界面的HTML文件
- `stocks.txt` - 批量查询的股票代码配置文件
- `requirements.txt` - Python依赖包列表

### CLI命令结构
主程序基于Click框架构建，包含以下主要命令：

1. **kline** - K线数据查询
   - 支持日期范围查询 (`--start`, `--end`, `--days`)
   - 支持CSV导出 (`--export`)
   - 自动统计分析和投资收益模拟

2. **info** - 股票基本信息查询
   - 公司信息、上市日期、行业分类等

3. **realtime** - 实时行情查询
   - 支持批量查询多只股票
   - 彩色显示涨跌情况

4. **finance** - 财务数据查询
   - 季度财务报表（利润表、资产负债表、现金流量表）
   - 支持年份和季度筛选 (`--year`, `--quarter`)

5. **index** - 指数成分股查询
   - 支持上证50、沪深300、中证500 (`--index`)
   - CSV导出功能

6. **batch** - 批量统计
   - 基于配置文件的批量股票分析
   - 默认读取 `stocks.txt`，支持自定义配置文件

### 股票代码格式化
工具支持多种股票代码格式：
- 完整格式：`sz.000001`（深交所）、`sh.600000`（上交所）
- 简写格式：`000001`（0/3开头自动识别为深交所）、`600000`（6开头自动识别为上交所）

### 数据处理流程
1. 登录baostock系统 (`bs.login()`)
2. 调用相应的查询API获取数据
3. 使用pandas进行数据处理和类型转换
4. 使用Rich库创建美化的表格显示
5. 可选的CSV导出功能
6. 登出系统 (`bs.logout()`)

## 配置文件格式

### stocks.txt 格式
```
sh.600000 # 浦发银行
sz.000002 # 万科A
sh.601398 # 工商银行
```

- 每行格式：`股票代码 + 空格 + # + 注释`（注释可选）
- 以 `#` 开头的行为注释行，会被忽略
- 空行会被忽略

## 常用开发命令

### 测试工具功能
```bash
# 测试K线数据获取
python stock.py kline 000001

# 测试批量统计
python stock.py batch

# 测试数据导出
python stock.py kline 000001 --export test.csv
```

### Web界面开发
```bash
# 运行Web界面（需要前端服务器在localhost:5173）
python pyweb.py
```

## 注意事项

- 数据来源：baostock（免费、稳定的A股数据接口）
- 更新频率：日线数据T+1更新，财务数据按季度更新
- 网络要求：需要稳定的网络连接获取数据
- Python版本：建议Python 3.7+
- 实时行情功能当前为演示版本，显示模拟数据