# MeshroomBatcher Roadmap

Here is a draft for some features that we would like to implement in MeshroomBatcher.

## Intelligent subtree fetcher

In the Entity Page, instead of fetching the whole tree:
- fetch the data for the first-level tree
- if the user clicks on a subtree, then fetch data from this subtree

This would help improve a lot the ImageFolder provider.

## Entity Page resize columns

Add controler on the tree view column width.

## Submit button on last page

On the last page we could add an `arrow forward` button that would launch the submit
process on scenes. It could be a global submit button and a single button per scene.

## Use graph inputs to parse scene params

For now additional parameters are exposed through the `parameters` attribute
on the `TemplateInfo` class, which means it needs to be set by the provider on the
`listAvailableTemplates` method.

Another way would be to use [`Graph Input` nodes](https://github.com/alicevision/Meshroom/pull/3164)
which provide a simple function to get exposed parameters. This way the exposed parameters
would be directly driven by the meshroom scene.

For now it is not used yet because this PR has not been approved yet.

## Redirect Meshroom logs to a new log UI.

Right now when we open a Meshroom scene after the instanciation took place, Meshroom logs
are mixed with MeshroomBatcher logs. We could add a new UI that would catch Meshroom's logs.
