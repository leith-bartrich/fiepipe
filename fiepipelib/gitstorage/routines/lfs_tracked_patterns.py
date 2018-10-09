from fiepipelib.gitstorage.routines.gitasset import GitAssetRoutines
import typing

def get_patterns(routines:GitAssetRoutines, patterns:typing.List[str]):

    #common image formats
    patterns.append("*.jpg")
    patterns.append("*.gif")
    patterns.append("*.bmp")
    patterns.append("*.png")
    patterns.append("*.psd")
    patterns.append("*.tga")
    patterns.append("*.tif")
    patterns.append("*.tiff")
    patterns.append("*.exr")
    patterns.append("*.cin")
    patterns.append("*.dpx")

    #common archive formats
    patterns.append("*.zip")
    patterns.append("*.tar")
    patterns.append("*.gz")
    patterns.append("*.7z")
    patterns.append("*.iso")
    patterns.append("*.dmg")

    #common audio formats
    patterns.append("*.mp3")
    patterns.append("*.m4a")
    patterns.append("*.wav")
    patterns.append("*.aif")
    patterns.append("*.aiff")
    patterns.append("*.wma")
    patterns.append("*.ac3")

    #common video formats
    patterns.append("*.mpg")
    patterns.append("*.avi")
    patterns.append("*.flv")
    patterns.append("*.mov")
    patterns.append("*.m4v")
    patterns.append("*.mp4")
    patterns.append("*.wmv")
    patterns.append("*.mxf")

    #common doc/publish formats
    patterns.append("*.pdf")
    patterns.append("*.eps")
    patterns.append("*.ai")
    #patterns.append("*.svg")

    #common MS working files
    patterns.append("*.doc")
    patterns.append("*.xls")
    patterns.append("*.ppt")

    #common 3d mesh files
    patterns.append("*.obj")
    patterns.append("*.fbx")

    #common executable files
    patterns.append("*.exe")
    patterns.append("*.com")
    patterns.append("*.bin")
    patterns.append("*.app")
    patterns.append("*.apk")
    patterns.append("*.jar")
    patterns.append("*.dll")
    patterns.append("*.so")
    patterns.append("*.lib")
    patterns.append("*.cab")
    patterns.append("*.sys")











