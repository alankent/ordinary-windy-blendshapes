# Create Blend Shapes for Windy Scenes

This project is designed for foliage such as grass, flowers, or trees so
it can sway in the wind in NVIDIA Omniverse. It is designed for models
that are static (unmoving).

It is a work in progress, but sharing where up to. I will probably potter
along with this in my spare time.

It works by creating blend shapes the move points in the mesh by an amount
proportional (with a bit of a curve) to the height of the point off the ground.
So points at (or below) ground level do not move. Points half way up move a
bit, points at the top move the most.

To use it,
* Create a new empty stage for your model, click the first "create skeleton" button which will define SkelRoot, Skeleton, and SkelAnimation prims.
* Add a reference to your model from under SkelRoot. It must be under this prim for it to animate.
* Click the second button which will create a blendshape for each mesh in the model.

## Plans

* Have 2 blend shapes for the model bending east and south. I want to create an animation graph that has two variables controlling the strength of the two blendshapes.
* I want to create an action graph that given wind direction, strength, sway speed etc animations the east and south weights (with negative values for west and north) so the foliage can sway in a specified direction
* I also want a central "wind" script that updates all of the individual models, so you can set the wind direction and strength centrally and everything in the stage will get updated
* I want to add another blendshape for a slight ripple, to make leaves flutter. This would be applied to selected meshes (leaves, not trunks or branches).


# Extension Project Template

This project was automatically generated.

- `app` - It is a folder link to the location of your *Omniverse Kit* based app.
- `exts` - It is a folder where you can add new extensions. It was automatically added to extension search path. (Extension Manager -> Gear Icon -> Extension Search Path).

Open this folder using Visual Studio Code. It will suggest you to install few extensions that will make python experience better.

Look for "ordinary.windy.blendshapes" extension in extension manager and enable it. Try applying changes to any python files, it will hot-reload and you can observe results immediately.

Alternatively, you can launch your app from console with this folder added to search path and your extension enabled, e.g.:

```
> app\omni.code.bat --ext-folder exts --enable company.hello.world
```

# App Link Setup

If `app` folder link doesn't exist or broken it can be created again. For better developer experience it is recommended to create a folder link named `app` to the *Omniverse Kit* app installed from *Omniverse Launcher*. Convenience script to use is included.

Run:

```
> link_app.bat
```

If successful you should see `app` folder link in the root of this repo.

If multiple Omniverse apps is installed script will select recommended one. Or you can explicitly pass an app:

```
> link_app.bat --app create
```

You can also just pass a path to create link to:

```
> link_app.bat --path "C:/Users/bob/AppData/Local/ov/pkg/create-2021.3.4"
```


# Sharing Your Extensions

This folder is ready to be pushed to any git repository. Once pushed direct link to a git repository can be added to *Omniverse Kit* extension search paths.

Link might look like this: `git://github.com/[user]/[your_repo].git?branch=main&dir=exts`

Notice `exts` is repo subfolder with extensions. More information can be found in "Git URL as Extension Search Paths" section of developers manual.

To add a link to your *Omniverse Kit* based app go into: Extension Manager -> Gear Icon -> Extension Search Path

