# Meshroom Batcher Documentation

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/meshroomHub/meshroomBatcher)

## How to setup

- You need Meshroom in your environment (correct `PYTHONPATH` environment variable set)
- You need to register the entity providers through the `MESHROOM_BATCHER_PROVIDERS` environment variable.
You can see an example [here](../../package.py)

## How does it work

When the tool is launched, it uses entity providers to fetch info. Each provider must implement method to provide:
- a list of templates
- an entity tree
- entities for a tree group

Then the UI launches.

<p align="center">
    <img width=800 src="./images/template_page.png" alt="Template selection" />
    <br/>
    <em>Template Selection UI : select the template to use.</em>
</p>

<p align="center">
    <img width=800 src="./images/entity_page.png" alt="Entities selection" />
    <br/>
    <em>Entity Selection UI : select entities to batch.</em>
</p>

<p align="center">
    <img width=800 src="./images/parameter_page.png" alt="Parameter Settings" />
    <br/>
    <em>Parameters UI : set values for exposed attributes.</em>
</p>


## Providers

**Mock Provider**

The mock provider is a provider that sets up fake data. It's main use is debugging and developping the app.
It also serves as a reference for implementing providers.

<p align="center">
    <img width=800 src="./images/mock_provider.png" alt="Mock provider" />
    <br/>
    <em>Mock provider.</em>
</p>

You can test it with the `--mock` command line argument. 
If you are testing inside meshroo (using the Batcher menu) you can obtain it by setting the `REGISTER_MOCK_ENTITYPROVIDER`
environment variable to `"1"`


**Image Provider**

This provider take a root folder and provide a file explorer that finds folders with images.

<p align="center">
    <img width=800 src="./images/imagefolder_provider.png" alt="ImageFolder provider" />
    <br/>
    <em>Image Folder provider.</em>
</p>

This require some setup :
- `MR_BATCHER_IMGFOLDER_ROOT`: the root folder where the file explorer starts.
- `MR_BATCHER_TEMPLATES_DIR`: a folder with Meshroom template files
- `MR_BATCHER_OUTPUT_ROOT`: The folder where instanciated files will be created

> [!WARNING]
> For now the tree view index all folder all at once, there's no smart update (we could implement it when we would expand a subtree it fetches folders then).
> This means you must avoid setting a big folder to `MR_BATCHER_IMGFOLDER_ROOT`, or this will take a lot of time indexing subfolders.



## How to implement a new Entity Provider

You can check [this page](./entityProviders.md)