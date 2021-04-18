# SSA HDRify

## 使用场景

在播放HDR视频时，由于屏幕会进入HDR，而SSA字幕格式又缺乏对应配置，字幕颜色通常会过饱和与过亮。

如果你播放HDR视频没有类似问题（比如用madVR将HDR tonemap到低亮度显示器），不建议使用这个脚本。

大佬们有[讨论过](https://github.com/libass/libass/issues/297)应对方式，不过在可见的未来不会有什么实质性进展。

短期内最简单的做法就是手工调整字幕的饱和度和亮度，达到不闪瞎狗眼的目的。


本脚本进行的操作如下

* 读取SSA文件并对颜色依次进行处理
* 字幕颜色使用BT.709 OETF线性化
* 由sRGB空间映射进xyY空间
* 调整Y亮度。例：sRGB亮度峰值为100nit，输出屏幕亮度峰值为1000nit，则Y*=0.1
  * 100nit与1000nit为默认值，CLI可调
* 由CIE xyY空间映射进BT2020空间
  * CLI可调为DCI-P3
* 使用PQ OETF做gamma correction
* 输出RGB

理论来说这个过程可以保证颜色准确性。但是由于字幕混合以及HDR显示的各种不确定性（比如色彩空间需要匹配HDMI的HDR元数据，而不一定是视频的色彩空间），处理过后的颜色仅能保证视觉效果不像处理前那么突兀。甚至可能出现在不同播放环境下字幕颜色完全不同的情况。

这个脚本对于各类对颜色准确度有要求的使用场景就完全无能为力了≡ω≡、。

## 使用方法

下载最新的[发行版](https://github.com/yyymeow/ssaHdrify/releases)

### 简易版

* 打开可执行文件
* 选择需要处理的字幕文件（可多选）
* 输出的字幕文件会使用.hdr.ass的扩展名

### CLI版

程序支持CLI模式，所有选项均为optional，缺失状态下会使用默认值。

`ssa_hdrify -s val -o val -c {dcip3,bt2020} -f file1 -f file2 ...`

* `-s --sub-brightness`
  * 字幕亮度峰值，默认 100 nit
  
	实际只会使用字幕与屏幕亮度比例，可以无视
* `-o --output-brightness`
  * 屏幕亮度峰值，默认 1000 nit
  
    如果输出字幕太亮，可以调高。反之亦然。
* `-c --colourspace`
  * 输出色域，可选值为 dcip3 与 bt2020，默认bt2020
    
	如果希望颜色更艳丽一些可以调为dcip3
	
* `-f --file`
  * 字幕文件，缺失状态下会弹出文件选择窗口。
  
    可通过使用多个-f 添加多个字幕文件。


## Background

When playing HDR videos, the display will be put into HDR mode. However, SSA subtitles lack the necessary info needed to be rendered properly in this environment, and as a result tend to be oversaturated and overly bright.

If you do not experience this issue, you do not need this script.

There has been some [discussions](https://github.com/libass/libass/issues/297) on how to extend SSA for this use case, but that seems to have staled, and no change is expected in the foreseeable future.

In the short term, a reasonble patch is to manually edit the colours in the SSA file to make it less blinding.

This script does the following

* Read the SSA file and process all colours used
* Convert RGB into linear space with BT.709 OETF
* Map it from sRGB into xyY space
* Adjust the luminance of the colour, Y
  * E.g., sRGB's peak brightness will be assumed to be 100nit, and the display 1000 nit, then Y*=0.1
  * 100 nit and 1000 nit are the default values respectively, and can be modified in CLI
* Map from CIE xyY into BT2020's RGB space
  * Can be adjusted to DCI-P3 in CLI
* Use PQ curve to apply gamma
* output RGB

Theoretically this is capable for preserving the actual colour of the subtitle. However, because of the complex pipeline of subtitle rendering/blending, and HDR displays in general, the end result is only something to the effect of "red is red and blue is blue". 

It's not suitable for anything that requires colour accuracy, e.g. subtitle colour matching.

## How to use

Download the latest [release](https://github.com/yyymeow/ssaHdrify/releases)

### Simple guide

* Run the program
* Select your subtitle files (you can select multiple)
* Modified subtitles will have the extension .hdr.ass

### CLI

The script supports some simple command line options. All arguments are optional.

`ssa_hdrify -s val -o val -c {dcip3,bt2020} -f file1 -f file2 ...`

* `-s --sub-brightness`
  * Peak brightness for subtitle. Default: 100 nit
  
    The important part is the ratio between screen and subtitle brightness.
	You should only need to change one of them.
* `-o --output-brightness`
  * Peak brightness for the display. Default: 1000 nit
  
    If the processed subtitle is too bright, increase this value, and vice versa.
* `-c --colourspace`
  * Output colourspace, value should be one of dcip3 and bt2020. Default: bt2020
  
    Use dcip3 if you prefer slightly more saturated colours.
	
* `-f --file`
  * Subtitle files. A popup will be used if this is missing.
  
    You can add multiple files by using multiple -f flags.
