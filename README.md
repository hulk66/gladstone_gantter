# Gladstone Gantter - a web application to draw Gantt Diagrams

Utlizing [Nicegui](https://nicegui.io/) and [Mermaid](https://mermaid.js.org/) 

* Editing Gantt Charts in a form based manner
* Entering start date and duration. End date will be calulated, excluding weekend. Or just provide the end date
* The end date is used as the start date for the next task
* Limited Color styling
* Loading and saving files to json to you local machine 
* Can be easly dockerized
## Example
![ ](form.png)

## Result
![Alt text](result.png)

## Setting up locally
1. Get the code from guthub
2. `conda env create -f env.yaml`
3. `conda activate gantt`
4. `python -m main.ui`

## Using the docker image
    docker run -p:8080:8080 hulk66/gladstone_gantter
Open http://localhost:8080    

## Issues
* Always fill name of swimlanes and tasks before switching to the diagram view. At the moment there is no validation. If not you get an error message on the diagram panel
* If you happen to see some text instead of the diagram, try a reload. Sometimes this does the trick


