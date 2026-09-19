# APEX GT-01 双座公路跑车

当前 CAD、STEP、STL 和 3MF 均已缩为原设计的 **60%**。切片软件保持 **100%** 导入，**不要再缩到 60%**。

侧放打印尺寸约 **119.7 × 32.4 × 56.4 mm**，小于 [A1 mini 的 180 × 180 × 180 mm 成型空间](https://us.store.bambulab.com/products/a1-mini)。3MF 是通用网格文件，不含打印机切片参数。

## 座舱、车窗和尾翼

- 主车身重新绘制为平顺的三次样条曲面，控制机盖与轮拱的高差，避免局部鼓包及深凹槽。前舱和后部的 14 条纵向采样线均无额外波谷；机盖与轮肩最大高差约 **2.12 mm**。
- 车头与车尾向端部渐降，最前、最后的底缘以相切曲线上收，减小厚重的垂直立面。端部中心截面厚度约为车头 **5.9 mm**、车尾 **6.2 mm**；前脸改为细长灯槽和单层宽进气口。轮拱与贴床区不随端部一起压扁。此项为外形调整，未进行风阻仿真。
- 前后四角改为渐变弧线收拢，纵向退让 **7.2 mm**、横向过渡 **14.4 mm**，保留 **56.4 mm** 的最大车宽。圆角在侧放方向逐层外扩，最大坡度控制为 45°。
- 车顶使用沿车长放样的圆弧截面，前后和横向均有弧度，最高点约 **32.4 mm**。
- 四个轮拱覆盖胎面上方，车轮保持转动间隙；沿胎宽和上部 120° 圆弧采样，壳体最薄约 **1.78 mm**，与胎面径向间隙 **0.9 mm**。
- 座舱后部延长为缓降的溜背曲面，逐渐接入后轮肩部与尾部平台，避免后风挡末端突然下落。
- 侧窗从靠近贴床面的外侧肩部起步，向车顶按约 **45°** 内倾；侧放后也是与热床约 45° 的斜面。中部窗下缘距热床约 **0.5 mm**，上部横向宽度约 **43.4 mm**，兼顾逐层成型和双座比例。
- 前后风挡、门窗和新增后侧小窗扩大了玻璃区域，保留连续的窄 A 柱、B 柱与 C 柱。报告记录各窗凹面之间的最小间距。
- 两侧固定车门带真实门缝和凹槽把手。门缝宽 **0.54 mm**，侧窗凹面和门缝横向切入 **0.48 mm**。
- 尾翼采用有弧度、后掠及向两端收窄的曲面翼型，配合翘起的后缘、短支柱和端板，最高点约 **29.4 mm**。翼面后缘厚 **0.96 mm**，端板与支柱名义厚 **1.2 mm**。端板内侧经 **4.8 mm** 翼展长度渐变连接翼面，避免侧放时突然伸出平板。
- 座舱按两个并排乘员参考包络检查：座位中心间距 **18 mm**、坐垫参考宽 **16.2 mm**，保留躯干、头部和腿部参考尺寸。检查仅用于外观比例，模型内部未制作座椅或驾驶设备，车门不可开启。

预览及 FreeCAD 中的深色玻璃是凹面的显示配色。单色 STL/3MF 不含透明玻璃或多色材料。预览采用实际 CAD 面的法线，保留真实曲面和特征边界，避免平整面被错误显示成凹陷。

## 前后贴床区域

前保险杠与后轮后方车尾永久加宽，两侧外缘与轮面同处一个侧放打印平面，无需拆除辅助片。

| 检查区域（输出坐标） | 实际平面贴床面积 |
| --- | ---: |
| 车头 X=48 至 60.3 mm | 约 83.9 mm² |
| 车尾 X=-60.6 至 -48 mm，Z<22.8 mm | 约 69.0 mm² |

车尾统计排除了车轮和尾翼，单独检查后保险杠。尾翼端板也接触同一打印平面，具体平面面积及 0.20 mm 首层平均截面积见验证报告。

`print_in_place/bed_contact_preview.png` 中，灰色为整车投影，绿色为车身首层，深灰色为轮组首层，黄色为前后保险杠的平面接触区域。

## 一体打印与检查

模型包含三个互不粘连的实体：一体车身、前轮组、后轮组。同轴左右轮一起转动，前后轴独立转动。

- 只导入 `print_in_place/apex_racer_side_down.stl` 或 `apex_racer.3mf`，保持侧放朝向和三个实体的相对位置。最低点已在 Z=0。
- 输出轴径 **5.4 mm**、孔径 **6.6 mm**，径向间隙 **0.6 mm**；轮胎与轮拱径向间隙 **0.9 mm**。这些间隙随整体同比缩放。
- 可从 0.4 mm 喷嘴、0.16–0.20 mm 层高、3 圈壁、15–20% 填充开始切片。检查首层门缝、轮面纹路和轮组间隙，避免象脚连住活动件。
- 按侧放无支撑目标设计：侧窗约 45°、车顶逐步收拢、前脸开口以 45° 收口，尾翼端板渐变展开，支柱及轮毂也采用斜面。门缝和把手的浅凹槽仍有短距离桥接；关闭支撑后检查这些细节的逐层预览，保持轮轴活动间隙通畅。附着不足时可给保险杠及尾翼端板增加外侧 brim。

`scripts/check_delivery.py` 检查保存的 CAD 实体、主曲面平顺性、四角收拢、前后端部厚度及渐薄截面、四轮上方壳体覆盖、后座舱过渡坡度、座舱弧面与宽度、双座参考包络、门缝、前后贴床面、尾翼、打印尺寸及 STL/3MF 一致性。生成脚本检查两根轴完整旋转包络与车身的间隙。

尚未实物试打；几何检查不能保证特定材料和打印机上的免支撑效果及转动手感。

本地 Bambu Studio 2.2.1.60 已使用 A1 mini / 0.4 mm 喷嘴、Generic PLA、0.20 mm 层高、3 圈壁及 15% 填充关闭支撑试切片，共 282 层。报告保存 STL 校验值，确认切片所用的就是当前模型；试切片产生的 G-code 仅用于本地检查。

## 文件与重新生成

- `apex_racer.FCStd`、`apex_racer.step`：60% 尺寸的直立 CAD 模型。
- `apex_racer.3mf`、`print_in_place/apex_racer_side_down.stl`：同尺寸的侧放打印模型。
- `apex_racer_preview.png`：前侧透视、侧视、后侧透视及俯视预览。
- `print_in_place/validation_report.json`：所有尺寸均以输出文件为准。
- `scripts/build_print_in_place.py`：构建、缩放和几何检查。
- `scripts/body_surface.py`：平顺主曲面、四角弧线以及曲面检查。
- `scripts/sports_coupe.py`：弧面座舱、窗面、车门、曲面尾翼及乘员参考包络。

代码内部仍使用原始设计坐标，通过 `MODEL_SCALE = 0.6` 整体缩放后输出。`scripts/build_racer.py` 只提供基础几何函数，不要单独运行它覆盖当前模型。

已验证环境为 Windows、FreeCAD 1.0.2 及其自带 Python 3.11；渲染还需要 NumPy、Pillow 和 Windows Arial 字体。在仓库根目录的 PowerShell 中执行：

```powershell
$freecadBin = 'D:\soft\FreeCAD 1.0\bin'
& "$freecadBin\python.exe" scripts/build_print_in_place.py
& "$freecadBin\FreeCADCmd.exe" scripts/export_current_3mf.py
& "$freecadBin\python.exe" scripts/render_racer.py
& "$freecadBin\python.exe" scripts/render_bed_contact.py
Start-Process -FilePath "$freecadBin\freecad.exe" -ArgumentList ('"' + (Join-Path $PWD 'scripts\save_display.FCMacro') + '"') -WindowStyle Hidden -Wait
& "$freecadBin\python.exe" scripts/check_slicing.py --bambu-dir 'D:\soft\Bambu Studio'
& "$freecadBin\python.exe" scripts/package_print.py
& "$freecadBin\python.exe" scripts/check_delivery.py
```

打印压缩包 `apex_racer_print_pack.zip`、中间场景 JSON 和 FreeCAD 自动备份不纳入 Git。如果本地已有压缩包，检查脚本也会验证它与当前打印文件完全一致。
