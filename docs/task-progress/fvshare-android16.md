# 任务进度：FVShare Android 16 适配

## 发布补充：用户真机验证

用户已确认 compat7 在小米14、小米17ultra、澎湃4.0.5.0 上扫描、连接、云台控制与拍摄均正常。该结论来自用户实际测试，发布助手未连接手机独立复测，不外推至其他设备或全部功能。下文保留开发历史和当时的待验证状态，最新发布状态以本节及仓库 README 为准。

- 状态：待验证
- 创建时间：2026-10-07
- 当前执行 Agent：OpenCode
- 用户授权：直接执行 APK 分析、修改和构建，无需交由 DSH。
- 工作区：非 Git 仓库。现有其他文档属于既有工作。

## 目标与恢复入口

输入为 `FVShare_2.4.5_APKPure.xapk`；原始提取 APK 为 `FVShare_2.4.5_original.apk`。目标是确认并修复 Android 16 安装及运行兼容性，支持 VILTA-M。恢复时先核对本文件、原包及实际修改，不覆盖原始文件。

## 已验证事实

- APK 包名 `com.freevisiontech.fvmobile`，版本 2.4.5，min SDK 21，target SDK 28。
- 包含 ARM64 库；其中 libmodft2、libmodpdfium、libmodpng 的 ELF LOAD 对齐为 4096，其他 ARM64 库为 65536。
- 有约 107 MB 的 OBB 扩展资源；实际资源用途尚未确认。
- 用户手机为小米 17 Ultra，Android 16 / 澎湃 OS 3.0.312.0；没有实际安装失败日志或连接的手机。
- 环境有 Python 3、Java/JDK 21；未发现 adb、apktool、jadx、apksigner、zipalign、Gradle 或 Android SDK CLI。
- 已通过 GitHub API 查询到 Apktool v3.0.3；尚未下载。

## 步骤

| 步骤 | 状态 | 验证 |
| --- | --- | --- |
| 分析清单、架构与库 | 进行中 | 已解析二进制清单及 ARM64 ELF 对齐；调用链待查 |
| 准备反编译与签名工具 | 进行中 | JDK 可用，其他工具待准备 |
| 确定兼容修复并构建 | 未开始 | 不得将盲目升级 target SDK 或替换库作为修复 |
| 验证 APK、交付与真机检查 | 未开始 | 真机需用户安装或连接 ADB |

## 最新执行结果

- 已生成 `FVShare_Android16_compat1.apk`，149349213 字节，SHA256 `e6691f35319546e7e375eb05a90dd525820442819361d1674a833ea5a7cbc62c`。
- 已新增 `prepare_compat.py`、`compat-build-report.json`、`docs/fvshare-android16-build.md`、`docs/pdfium-candidate-LICENSE.txt`。
- 构建指导及实际修改记录：`docs/fvshare-android16-build.md`。
- 已用 Apktool 3.0.3 完成 Smali/资源构建，uber-apk-signer 1.3.0 完成对齐及 v1/v2/v3 签名验证。工具提示一条未展开 warning。
- 全部打包 ARM64 ELF 满足 16 KB 段对齐，ZIP CRC 和本地库依赖名称检查通过；native 库压缩，内置音频不压缩。
- 新库固定提交 `8037a684c47fec2e62ec3e9e89e616eac0d596dd`，Java native 参数及全部旧 JNI 导出已核对。
- 三个 OBB 固件资源与 APK 冲突，保留 APK 原始文件，见构建报告。
- 修改脚本首次遇到资源冲突停止，之后修订为保留 APK 优先资源；PDF 加载器修改重复检查已加入。YAML 修改不应对同一树重复运行。
- 原始输入和现有模型配置文档保留；非 Git 仓库无法使用 Git diff。
- 临时签名密钥：`/tmp/opencode/fvshare-compat.keystore`，后续版本必须保存并复用，避免签名变化。

## 当前步骤状态

| 步骤 | 状态 | 验证 |
| --- | --- | --- |
| 静态分析与调用链确认 | 已完成 | PDF JNI、assets 优先加载、权限请求已阅读 |
| 工具准备 | 已完成 | Apktool、签名工具可执行 |
| 局部依赖升级及兼容构建 | 已完成 | 构建和签名检查通过 |
| Android 16 真机启动及云台验收 | 待验证 | 未连接手机，未执行 |

## 下一步

用户覆盖安装 `FVShare_Android16_compat7.apk` 并记录阶段码；5001=唯一原版已知服务已选定，-5001=无已知服务，-5002=多个已知服务不自动选择。随后检查3003、4001、2000及界面是否完成初始化。若无已知服务，需要实际服务UUID表，不猜测控制服务。

## 第七版已知服务匹配修复

- 用户报告-3002：实际GATT表缺少App所选服务。已确认服务选择不匹配，尚未确定实际型号服务UUID。
- 新增 patch_service_selection.py，在初始化前枚举原版BleConstant.SERVICE_UUIDS中的三个服务；仅唯一实际存在时更新SERVICE_UUID_CONFIG和GET_CURRENT_PTZ_UUID，不修改型号、固件或协议指令。
- 可能仍存在错误页面对应协议初始化的问题，需要后续真机验证；多个或未知服务时只报告不推定。
- 脚本、Apktool强制构建、签名v1/v2/v3、对齐、ZIP CRC通过。
- 产物 `FVShare_Android16_compat7.apk`，149349213字节，SHA256 `a153c92b239795f59a2c2a8f3db6bcb9d4dd4f0b4ab1cd3cd0118e7b7f7703c3`。恢复顺序在第六版后追加patch_service_selection.py一次。

## 第六版初始化诊断

- 用户确认服务发现成功后仍自动连接中。
- 新增 `patch_init_diagnostics.py`，在成功服务发现后检查所选服务及WRITE/NOTIFY属性，诊断通知请求入队和描述符写结果；不更改UUID或绕过握手。
- 执行脚本、Apktool强制构建、对齐、v1/v2/v3签名及ZIP CRC检查通过。
- 产物 `FVShare_Android16_compat6.apk`，149349213字节，SHA256 `6ff94a5e92ab2ce17fd17b5b034278e2c88ef7e24d2d8290ccea96af83dd635`；真机结果待用户提供。
- 恢复构建在第五版顺序后增加 patch_init_diagnostics.py 一次。

## 第五版真机反馈与后续核查

- 用户报告1001后stage/code=0：链路及服务发现均确认成功；不能据此认定协议初始化完成。
- 已阅读 FVPTZFragment.getGattSerAndChaAndNotify、receiveEvent及onDescriptorWrite：服务严格匹配SERVICE_UUID_CONFIG；特征按WRITE/NOTIFY属性筛选；描述符写回调忽略status并发送初始化事件。可能存在型号选择不匹配或订阅失败，但没有实际服务表/订阅结果，未确认根因。
- 本轮未新增APK，避免在无实际初始化证据情况下继续替换连接参数。

## 第五版诊断线程修正（2026-10-07）

- 用户报告 `status=0, state=2`，已确认链路连接成功。服务发现尚未确认。
- 复查发现第三版 reportGattStage 在蓝牙回调线程直接调用 Toast，可能抛出线程异常并阻止随后 discoverServices；属于本任务引入的回归，是否在真机确实抛出仍无日志确认。
- 新增 `patch_gatt_diagnostics.py`，reportGattStage 使用第四版的 CompatBleToast Runnable，经 runOnMainThread 调度，不直接在回调线程执行 Toast。
- 脚本执行、Apktool强制构建、签名v1/v2/v3、对齐和ZIP CRC检查通过。没有真机运行验证。
- 产物 `FVShare_Android16_compat5.apk`，149349213字节，SHA256 `955664c2841bc74ebfacba8dcfbeb5ce6e7da7b2279ce73498f3966a184d326f`。
- 恢复构建在第四版顺序后执行 patch_gatt_diagnostics.py 一次，再强制构建与原密钥签名。

## 第四版超时界面与诊断（2026-10-07）

- 用户反馈第三版连接超时且自动连接提示持续，云台红灯闪烁；红灯含义未核验。
- 核查 FVPTZFragment.receiveEvent：超时分支关闭加载框，但不隐藏自动连接提示，与断开分支行为不一致。
- 新增 `patch_timeout.py`：超时后清除 isAutoConnect 并隐藏自动连接提示；所有链路回调显示 status/newState，提示通过主线程 Runnable 发送。第三版的阶段 Toast 仍保持原实现。
- 不宣称物理连接已修复；这版解决已定位的界面遗漏并增强诊断。
- 修改脚本、Apktool强制构建、uber-apk-signer v1/v2/v3和对齐、ZIP CRC检查通过。产物 `FVShare_Android16_compat4.apk`，149349213字节，SHA256 `86f780e88875c588c0db2bcf457d146012aa59e11910a5786b8ce9e6c93f296e`。
- 恢复时按第三版顺序增加 patch_timeout.py 一次，仍复用签名密钥。

## 第三版 GATT 修复（2026-10-07）

- 用户确认第二版能扫描，连接后一直显示连接设备中；扫描真机验证通过，连接尚未通过。
- 已阅读 `ViseBluetooth.connect`、`ViseBluetooth$2.onConnectionStateChange/onServicesDiscovered`、超时 Handler、服务特征选择及通知订阅。
- 新增 `patch_gatt.py`：BLE transport 明确设为 2，使用 autoConnect=false；立即保存 pending GATT，使现有超时可关闭；移除服务发现成功后的隐藏缓存 refresh 调用；新增连接/服务发现阶段提示。
- 不能确认这就是实际卡顿根因；未获得运行日志，通知订阅和握手仍待检查。
- 执行修改脚本、Apktool `b -f` 构建及 uber-apk-signer 对齐/v1/v2/v3 签名验证成功，ZIP CRC 通过。签名证书与前版相同。
- 产物 `FVShare_Android16_compat3.apk`，149349213 字节，SHA256 `a385d6fd6dfda330b4d089377c8fa68e60ae39f9e9b5506bc05bfac64693b547`，计划版本代码247、名称2.4.5-a16-compat3，使用强制重建资源，尚未重新解析成品清单。
- 恢复构建顺序：原包解码 → prepare_compat.py → patch_ble.py → patch_gatt.py，各执行一次 → Apktool强制构建 → 相同密钥签名。

## 第二版 BLE 修复（2026-10-07）

- 用户反馈第一版扫描不到云台。第一版未完整核查蓝牙过滤，第二版已阅读 `ViseBluetooth`、`PeriodLScanCallback`、`FVPTZFragment$3`、`FVMainForSearchBluetooth$7` 及 `BluetoothLeDevice`。
- 新增 `patch_ble.py`：取消扫描阶段按当前页面的单 UUID 过滤；统一使用低延迟扫描参数；设备名优先取广告完整/短名称，再取缓存；空 ScanRecord 防护；新增异步扫描失败码日志和提示。
- 原有 VILTA 名称筛选及 GATT 控制协议保留。没有真机广播或权限日志，以上是兼容修复与诊断增强，非确认根因。
- 运行 `python3 patch_ble.py /tmp/opencode/fvshare-decoded` 成功；Apktool 首次增量构建没有重建清单，随后以 `b -f` 全量重建并重新签名。二进制清单确认 versionCode 246、versionName 2.4.5-a16-compat2。
- uber-apk-signer 对齐及 v1/v2/v3 签名验证通过；证书与第一版相同，可覆盖更新。ZIP CRC 通过。
- 产物 `FVShare_Android16_compat2.apk`，149349213 字节，SHA256 `baf32b470e8b22d61783f4cfacb9f87219c453c4d20ffc7d3c03ebc74e709b0d`。
- 验证脚本首次将清单中的字符串版本代码与整数比较导致断言失败；输出已显示实际值 246，此为检查脚本类型错误，不是包错误。
- 恢复时从原 APK 解包，执行 prepare_compat.py 一次，再执行 patch_ble.py 一次，使用 Apktool `b -f` 构建；不要重复应用 patch_ble.py。

## 风险与限制

只有二进制安装包，没有原厂源码、依赖声明或构建项目；不能承诺所有依赖可升级。签名变更可能影响原有签名校验及更新。没有真机不能声称 Android 16 验证通过。
