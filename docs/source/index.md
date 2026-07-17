# Meshroom Batcher Documentation

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


## How to implement a new Entity Provider

You can check [this page](./entityProviders.md)