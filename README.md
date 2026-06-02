# Cellular Modem Control

Cross-platform Python tools for controlling cellular modules over a serial
AT-command port. The project uses standard modem commands by default and keeps
vendor-specific behavior behind profiles.

中文说明见 [中文](#中文).

The default Windows port is `COM8`. Override it for Linux/macOS devices such as
`/dev/ttyUSB2`, `/dev/ttyACM0`, or `/dev/cu.usbserial-*`.

## Project Status

This project is pre-1.0 and suitable for early open-source use. The generic AT
core, no-hardware tests, packaging checks, dry-run safety checks, and one local
Quectel EC600N smoke validation are in place. Hardware-specific behavior should
continue to be added through profiles and reproducible reports.

## Standard Core

These operations are implemented with common Hayes/3GPP-style AT commands:

- Probe module identity, SIM/network signal, and raw AT commands.
- Send, list, read, and delete SMS messages in text mode.
- Use UCS2 SMS encoding for non-ASCII text such as Chinese.
- Dial, answer, hang up, list active calls, and send DTMF.
- Monitor unsolicited modem events such as incoming calls and new SMS notices.

## Vendor Profiles

The CLI defaults to `--profile generic`. Use profiles for vendor-specific
extensions while keeping the common API stable:

- `generic`: standard AT commands for broad modem compatibility.
- `quectel`: Quectel-compatible profile. It currently uses the same standard
  commands and is ready for model-specific audio routing extensions.

Actual call audio is hardware dependent. Most modules do not carry live voice
audio over the AT serial port. Use the module's USB Audio, PCM/I2S, or analog
audio interface according to the exact module datasheet.

## Quick Start

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

Without installing the package, run from this repository:

```powershell
$env:PYTHONPATH="src"
python -m cellular_modem.cli --port COM8 info
```

The older `python -m quectel_modem.cli ...` entry point is kept as a compatibility
alias.

## Documentation

- [Architecture](docs/architecture.md)
- [CLI reference](docs/cli.md)
- [Python API](docs/api.md)
- [Examples](docs/examples.md)
- [Hardware notes](docs/hardware.md)
- [Profiles](docs/profiles.md)
- [Compatibility](docs/compatibility.md)
- [Codex skills](docs/skills.md)
- [Testing](docs/testing.md)
- [Maintenance](docs/maintenance.md)
- [Release process](docs/release.md)
- [Contributing](CONTRIBUTING.md)
- [Support](SUPPORT.md)
- [Security policy](SECURITY.md)

## Useful Commands

```powershell
modemctl ports
modemctl --port COM8 raw "ATI"
modemctl --port COM8 smoke --json
modemctl --port COM8 sms-send "+8613800138000" "test" --dry-run
modemctl --port COM8 sms-send "+8613800138000" "Chinese text" --encoding ucs2 --dry-run
modemctl --port COM8 sms-list
modemctl --port COM8 sms-read 1
modemctl --port COM8 sms-delete 1 --dry-run
modemctl --port COM8 call-answer --dry-run
modemctl --port COM8 dtmf "123#" --dry-run
modemctl --port COM8 audio-volume 70 --dry-run
modemctl --port COM8 audio-mute on --dry-run
modemctl --port COM8 monitor --enable-events
```

## Safety

Sending SMS and placing calls may incur carrier charges. The CLI only performs
those actions when the command explicitly asks for them.

Use `--dry-run` on state-changing commands such as `sms-send`, `sms-delete`,
`call-dial`, `call-answer`, `call-hangup`, `dtmf`, `audio-volume`, and
`audio-mute` to preview the operation without opening the serial port.

Use `modemctl --port COM8 smoke --json` for a read-only hardware validation
report. It runs open/init/info/SIM/signal/ATI checks and redacts modem
identifiers by default.

For issue reports, use `modemctl --port COM8 smoke --format markdown`.

## Development

```powershell
python -m pip install -e ".[dev]"
python scripts/check.py
```

## 中文

`cellular-modem-control` 是一个跨平台 Python 项目，用串口 AT 指令控制蜂窝
通信模块。项目默认使用通用标准 AT 指令，并通过 profile 隔离厂商或型号相关
行为，适合后续逐步扩展到 Quectel、SIMCom、Fibocom、Sierra、Telit、u-blox
等模块。

Windows 默认端口是 `COM8`。Linux/macOS 可以使用 `/dev/ttyUSB2`、
`/dev/ttyACM0`、`/dev/cu.usbserial-*` 等实际 AT 端口。

### 项目状态

当前项目处于 pre-1.0 阶段，可以作为早期开源项目上传。已经具备通用 AT 核心、
无硬件单元测试、打包校验、dry-run 安全检查、文档链接检查、文档 CLI 示例
校验，以及本机 Quectel EC600N 的只读 smoke 验证。后续硬件或厂商差异应继续
通过 profile 和可复现 issue 逐步迭代。

### 标准能力

这些能力基于常见 Hayes/3GPP 风格 AT 指令：

- 查询模块身份、SIM 状态、网络信号和 raw AT 指令。
- 以文本模式发送、列出、读取和删除短信。
- 使用 UCS2 编码发送中文等非 ASCII 短信。
- 拨号、接听、挂断、列出通话和发送 DTMF。
- 监听来电、新短信等 unsolicited modem events。

### 厂商 Profile

CLI 默认使用 `--profile generic`。当模块需要厂商特定扩展时，通过 profile 增加
行为，保持通用 API 稳定：

- `generic`：面向广泛兼容性的标准 AT 指令。
- `quectel`：Quectel 兼容 profile。目前复用 generic 指令集，是后续添加型号
  特定音频路由或诊断指令的扩展点。

注意：AT 串口通常只控制通话状态，不传输实时语音。通话音频需要根据具体模块
数据手册使用 USB Audio、PCM/I2S 或模拟音频接口。

### 快速开始

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

### 文档

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

### 常用命令

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

### 安全边界

发送短信和拨打电话可能产生运营商费用。CLI 只有在命令明确要求时才会执行这些
动作。

对 `sms-send`、`sms-delete`、`call-dial`、`call-answer`、`call-hangup`、
`dtmf`、`audio-volume`、`audio-mute` 等会改变状态的命令，先使用 `--dry-run`
预览操作。dry-run 不会打开串口。

使用 `modemctl --port COM8 smoke --json` 生成只读硬件验证报告。该报告会执行
open/init/info/SIM/signal/ATI 检查，并默认脱敏 modem 标识符。

提交 issue 时，建议使用 `modemctl --port COM8 smoke --format markdown`。

### 开发

```powershell
python -m pip install -e ".[dev]"
python scripts/check.py
```
