# Tools-for-Models
Written to help automate preparation of models created in Masterpiece VR. This add-on does (optionally) all of the recommended steps from this forum post by one of the Masterpiece VR developers:  http://forum.masterpiecevr.com/t/how-to-uv-unwrap-an-exported-mpvr-model-in-blender/135 

# Functions (as of v0.7):
* Remove doubles from all meshes in a scene, given minimum distance.
* Decimate all meshes, optionally triangulating and mirroring along specified plane.
* Undecimate all meshes.
* Smart UV Project, with the option to delete existing UV maps and recreating new ones. If you run without the "Delete UV Maps" box ticked then it runs the UV project only on meshes that do not already have a UV map.

# Installation
Simply open the script in a Blender text editor window and click "Run Script". (If you don't know how to do that, see below.)

You should immediately see a panel at the bottom of the Tools tab in any 3D View that looks like this:
![Alt text](https://github.com/lelandg/Tools-for-Models/blob/master/2018-02-04%2007_06_31-Blender.png)
(I've moved it to the top of my Tools panel. You can do that if you'd like.)

If you need help beyond this (below), I could create a video tutorial if needed. I'm looking into making this an "official" add-on, but have no idea of the process.

For now, if you hold your mouse cursor over the 3D view and press CTRL-right twice, you should get the code workspace. There you should see the text editor. At the bottom of that window there is a menu, and you want Text->Open Text Block. Then navigate to the.py file that you downloaded and open it. You should then see the "Run Script" button.

Note that at the top of the code work space, there is a console output that will show the status. But if you click the Remove Doubles Globally button, it will also print an information message at the very end and tell you how many meshes it processed and how many verts it removed.

If you tick the 'Register' checkbox at the bottom of your text window, it will automatically run the script the next time you open this blend file. Note that you may get an error when you do this. If so, you can click the "Reload Trusted" button at the top of the window. That will allow you to actually auto-register the script every time you load the Blender file.

![Alt text](https://github.com/lelandg/Tools-for-Models/blob/master/2018-01-30%2007_49_41-Blender_%20%5BE__Documents_Blender_Wasp%20Spaceship%2002%20-%20Fresh%20import%20for%20tutorial.ble.png)

If you want the script to always load at startup, you can import it as an add-on (I think... I'll look into this later), or open your startup scene, open the textblock and take the "Register" box and then save the startup scene (File -> Save Startup File). This latter method is confirmed by me to work, so I'd recommend that until I look into actual Blender plugins.

# Usage
Make sure you're not in Edit mode and then just change the settings and click the buttons to execute.

# Future Plans
None at the moment. Should this panel do anything else? You're welcome to create an Issue here (to help me remember feature suggestions).
