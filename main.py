from fastapi import FastAPI ,Path, HTTPException,Query
from fastapi.responses import JSONResponse
import json
from pydantic import BaseModel ,Field,computed_field
from typing import Annotated,Literal,Optional

app= FastAPI()

class Patient(BaseModel):
    id: Annotated[str,Field(...,description='Id of the patient',examples=['P001'])]
    name: Annotated[str,Field(...,description='Name of the patient')]
    city:Annotated[str,Field(...,description='City of the patient where he is living ')]
    age:Annotated[int,Field(...,gt=0,lt=100,description="Age of the patient ")]
    gender:Annotated[Literal['male','female','others'],Field(...,description='Gender of the patient ')]
    height:Annotated[float,Field(...,gt=0,description='Height of the patient in mtrs')]
    weight:Annotated[float,Field(...,gt=0,description='weight of the patient in kgs')]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi= round(self.weight/(self.height**2),2)
        return bmi

    @computed_field
    @property
    def verdict(self) ->str:
        if self.bmi <18.5:
            return 'underweight'
        elif self.bmi < 25:
            return 'Normal'
        elif self.bmi <30:
            return 'Over-weight'
        else:
            return "obese"

        
class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None, description='Name of the patient')]
    city: Annotated[Optional[str], Field(default=None, description='City of the patient where he is living')]
    age: Annotated[Optional[int], Field(default=None, gt=0, lt=100, description="Age of the patient")]
    gender: Annotated[Optional[Literal['male','female','others']], Field(default=None, description='Gender of the patient ')]
    height: Annotated[Optional[float], Field(default=None, gt=0, description='Height of the patient in mtrs')]
    weight: Annotated[Optional[float], Field(default=None, gt=0, description='weight of the patient in kgs')]

def load_data():
    with open('patients.json','r') as f:
        data = json.load(f)
    return data

def save_data(data):
    with open('patients.json','w')as f:
        json.dump(data,f)


@app.get("/")
def hello():
    return {'message':'Patient Management System API'}

@app.get("/About")
def About():
    return{"message":"A fully functional API to manage your patient recors"}

@app.get("/view")
def view():
    data = load_data()

    return data 

@app.get('/patient/{patient_id}')
def view_patient(patient_id:str = Path(..., description = 'Id of the patient in the Database ',example='P001')):
    #load all patients
    data= load_data()

    if patient_id in data:
        return data[patient_id]
    return HTTPException(status_code=400,detail='Patient not found')

@app.get('/sort')
def sort_patients(sort_by:str=Query(...,description='sort on the basis of height ,weight or bmi'),order:str= Query('asc',description = 'sort in asc or desc order ')):
   
    valid_fields= ['height','weight','bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400,detail =f'Invalid field select from {valid_fields}')
    
    if order not in ['asc','desc']:
        raise HTTPException(status_code=400, detail = 'Invalid order select between as or desc')
    
    data = load_data()

    sort_order = True if order == 'desc' else False 

    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by, 0), reverse=sort_order)

    return sorted_data

@app.post('/create')
def create_patient(patient:Patient):

    #load the existing data 
    data= load_data()
    #check if the patient is already exists
    if patient.id in data:
        raise HTTPException(status_code=400,detail='Patient already registred')
    #new patient added to the database
    data[patient.id]=patient.model_dump(exclude=['id'])

    # save in the json file
    save_data(data)

    return JSONResponse(status_code=201,content={'message':'patient created sucessfully'})

@app.put('/edit/{patient_id}')
def update_patient(patient_id:str,patient_update:PatientUpdate):

    data=load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404,detail='Patient not found')

    #update the patient data
    existing_patient_info = data[patient_id]

    updated_patient_info = patient_update.model_dump(exclude_unset=True)

    for key ,value in updated_patient_info.items():
        existing_patient_info[key]=value
    
    #existing_patient_info -> pydantic object -> updated bmi +verdict
    existing_patient_info['id']=patient_id
    
    patient_pydantic_obj = Patient(**existing_patient_info)


    #-> pydantic object -> dict
    existing_patient_info = patient_pydantic_obj.model_dump(exclude='id')

    data[patient_id]=existing_patient_info

    # Save the updated data back to the JSON file
    save_data(data)

    return JSONResponse(status_code=200, content={'message': 'Patient updated successfully'})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id:str):
    data=load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404,detail='Patient not found')

    #delete the patient from the database
    del data[patient_id]

    #save the updated data back to the JSON file
    save_data(data)

    return JSONResponse(status_code=200,content={'message':'Patient deleted successfully'})