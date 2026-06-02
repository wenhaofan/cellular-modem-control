# Cellular Modem Control

语言 / Language: 中文 | [English](README.en.md)

`cellular-modem-control` 是一个跨平台 Python 项目，用串口 AT 指令控制蜂窝
通信模块。项目默认使用通用标准 AT 指令，并通过 profile 隔离厂商或型号相关
行为，适合后续逐步扩展到 Quectel、SIMCom、Fibocom、Sierra、Telit、u-blox
等模块。

它也可以作为 agent 通信能力的底层工具：Codex、Claude、CrawBot、Hermes 或
其他 AI agent / automation agent 可以通过 CLI、Python API 或 skill 封装调用
它，让本地蜂窝模块具备真实手机号的短信收发、拨号、接听、挂断、DTMF 和事件
监听能力。

Windows 默认端口是 `COM8`。Linux/macOS 可以使用 `/dev/ttyUSB2`、
`/dev/ttyACM0`、`/dev/cu.usbserial-*` 等实际 AT 端口。

## 项目状态

当前项目处于 pre-1.0 阶段，可以作为早期开源项目上传。已经具备通用 AT 核心、
无硬件单元测试、打包校验、dry-run 安全检查、文档链接检查、文档 CLI 示例
校验，以及本机 Quectel EC600N 的只读 smoke 验证。后续硬件或厂商差异应继续
通过 profile 和可复现 issue 逐步迭代。

## 一键安装

先 clone 仓库，然后在项目根目录运行对应脚本。默认会创建或刷新 `.venv`、
执行 `pip install -e .`，并把 bundled Codex skills 安装到 `$CODEX_HOME/skills`
或 `~/.codex/skills`。

Windows PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

Linux/macOS：

```bash
bash scripts/install.sh
```

安装前预览将要执行的 package 和 skill 安装动作：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -DryRun
```

只安装或刷新 agent skill：

```powershell
python scripts/install_skills.py --dry-run
python scripts/install_skills.py --skill cellular-at-modem
python scripts/install_skills.py --skill quectel-modem
```

`cellular-at-modem` 适合通用 AT modem，`quectel-modem` 适合 Quectel 模块。
安装后，Codex 或其他支持本地 skill 的 agent 可以把它作为“短信/电话/AT modem
工具说明书”加载，再调用 `modemctl` 或 Python API。

## 标准能力

这些能力基于常见 Hayes/3GPP 风格 AT 指令：

- 查询模块身份、SIM 状态、网络信号和 raw AT 指令。
- 以文本模式发送、列出、读取和删除短信。
- 使用 UCS2 编码发送中文等非 ASCII 短信。
- 拨号、接听、挂断、列出通话和发送 DTMF。
- 监听来电、新短信等 unsolicited modem events。

## 适用场景

- 为 Codex、Claude、CrawBot、Hermes 等 agent 增加可审计的 phone call / SMS
  tool，让自动化任务能够通过真实蜂窝网络通知、确认或交互。
- 把 Quectel、SIMCom、Fibocom、Sierra、Telit、u-blox 等蜂窝模块封装为本地
  communication skill，用于 AI agent、机器人、IoT 网关或实验室自动化。
- 构建短信验证码测试、短信告警、电话提醒、外呼确认、DTMF IVR 测试、来电和
  新短信事件监听等工作流。
- 在没有云短信或云语音服务的场景下，用本地 SIM 卡和 AT modem 提供跨平台的
  fallback communication channel。

## 搜索关键词

AI phone call skill, agent phone call tool, SMS agent, Codex skill, Claude
tool, CrawBot, Hermes agent, AT command modem, GSM modem Python, LTE modem
control, cellular modem CLI, Quectel SMS, SIMCom modem, voice call AT commands,
DTMF modem, serial modem automation.

## 使用演示

只读硬件验证，适合作为 issue 或兼容性报告：

```powershell
modemctl --port COM8 --profile generic smoke --json
modemctl --port COM8 --profile generic info
modemctl --port COM8 signal
```

给 agent 预览短信、拨号和 DTMF 动作：

```powershell
modemctl --port COM8 sms-send "+8613800138000" "Codex task finished" --dry-run
modemctl --port COM8 call-dial "+8613800138000" --dry-run
modemctl --port COM8 dtmf "123#" --dry-run
modemctl --port COM8 call-hangup --dry-run
```

监听来电和新短信事件：

```powershell
modemctl --port COM8 monitor --enable-events
```

Python 只读 smoke 示例：

```python
from cellular_modem import report_to_markdown, run_read_only_smoke

report = run_read_only_smoke(port="COM8", profile="generic")
print(report_to_markdown(report))
```

Agent 可以把上面的 CLI 包装成 tool，例如：

- 任务完成后，通过短信 dry-run 生成可审计计划，再由用户确认是否真实发送。
- 监控任务失败时，拨打电话提醒负责人。
- 接入 IVR 测试时，拨号后发送 DTMF。
- 监听来电或新短信，把外部手机号事件转成 agent workflow 输入。

## 厂商 Profile

CLI 默认使用 `--profile generic`。当模块需要厂商特定扩展时，通过 profile 增加
行为，保持通用 API 稳定：

- `generic`：面向广泛兼容性的标准 AT 指令。
- `quectel`：Quectel 兼容 profile。目前复用 generic 指令集，是后续添加型号
  特定音频路由或诊断指令的扩展点。

注意：AT 串口通常只控制通话状态，不传输实时语音。通话音频需要根据具体模块
数据手册使用 USB Audio、PCM/I2S 或模拟音频接口。

## 快速开始

```powershell
python -m pip install -e .
modemctl ports
modemctl --port COM8 --profile generic smoke --json
modemctl --port COM8 --profile generic info
modemctl --port COM8 signal
modemctl --port COM8 sms-send "+8613800138000" "test" --dry-run
modemctl --port COM8 call-dial "+8613800138000" --dry-run
modemctl --port COM8 call-hangup --dry-run
```

不安装包时，可以在仓库根目录直接运行：

```powershell
$env:PYTHONPATH="src"
python -m cellular_modem.cli --port COM8 info
```

旧入口 `python -m quectel_modem.cli ...` 仍保留为兼容别名。

## 文档

- [架构](docs/architecture.md)
- [CLI 参考](docs/cli.md)
- [Python API](docs/api.md)
- [示例](docs/examples.md)
- [硬件说明](docs/hardware.md)
- [Profiles](docs/profiles.md)
- [兼容性](docs/compatibility.md)
- [Codex skills](docs/skills.md)
- [测试](docs/testing.md)
- [维护](docs/maintenance.md)
- [发布流程](docs/release.md)
- [贡献指南](CONTRIBUTING.md)
- [支持范围](SUPPORT.md)
- [安全策略](SECURITY.md)

## 常用命令

```powershell
modemctl ports
modemctl --port COM8 raw "ATI"
modemctl --port COM8 smoke --json
modemctl --port COM8 sms-send "+8613800138000" "test" --dry-run
modemctl --port COM8 sms-send "+8613800138000" "中文测试" --encoding ucs2 --dry-run
modemctl --port COM8 sms-list
modemctl --port COM8 sms-read 1
modemctl --port COM8 sms-delete 1 --dry-run
modemctl --port COM8 call-answer --dry-run
modemctl --port COM8 dtmf "123#" --dry-run
modemctl --port COM8 audio-volume 70 --dry-run
modemctl --port COM8 audio-mute on --dry-run
modemctl --port COM8 monitor --enable-events
```

## 安全边界

发送短信和拨打电话可能产生运营商费用。CLI 只有在命令明确要求时才会执行这些
动作。

对 `sms-send`、`sms-delete`、`call-dial`、`call-answer`、`call-hangup`、
`dtmf`、`audio-volume`、`audio-mute` 等会改变状态的命令，先使用 `--dry-run`
预览操作。dry-run 不会打开串口。

使用 `modemctl --port COM8 smoke --json` 生成只读硬件验证报告。该报告会执行
open/init/info/SIM/signal/ATI 检查，并默认脱敏 modem 标识符。

提交 issue 时，建议使用 `modemctl --port COM8 smoke --format markdown`。

## 开发

```powershell
python -m pip install -e ".[dev]"
python scripts/check.py
```
