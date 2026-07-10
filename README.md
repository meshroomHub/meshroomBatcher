<div align="center">
  <img src="logo.svg" width="250"/>
  <h1 style="font-size: value;">Meshroom Batcher</h1>
  <i>Pipeline Batcher for Meshroom</i>
  <br/>
  <br/>
</div>

This package contains components that implement a Batcher UI for Meshroom.
The goal is to provide a UI inside Meshroom where users can create and launch a batch of scenes from different source entities.

## How does it work

When the tool is launched, it uses entity providers to fetch info. Each provider must implement method to provide:
- a list of templates
- an entity tree
- entities for a tree group

Then the UI launches.

<p align="center">
    <img width=800 src="./docs/images/template_page.png" alt="Template selection" />
    <br/>
    <em>Template Selection UI : select the template to use.</em>
</p>

<p align="center">
    <img width=800 src="./docs/images/entity_page.png" alt="Entities selection" />
    <br/>
    <em>Entity Selection UI : select entities to batch.</em>
</p>

<p align="center">
    <img width=800 src="./docs/images/parameter_page.png" alt="Parameter Settings" />
    <br/>
    <em>Parameters UI : set values for exposed attributes.</em>
</p>


## How to implement a new Entity Provider

