"""
    Imports customers from Close RMC to the database
    :license: MIT
"""
import uuid
import os
import datetime
import json
from src.dependencies.requests_provider import get_requests_provider
from src.dependencies.pynamodb_customers_provider import get_customers_provider
from src.dependencies.pynamodb_contract_provider import get_contracts_provider
from src.dependencies.pynamodb_consultant_provider import get_consultants_provider


def get(event, context):
    ''' AWS Event Handler '''
    print("Context: ", context)
    print("Event: ", event)
    requests_client = get_requests_provider()
    customer_model = get_customers_provider()
    consultant_model = get_consultants_provider()
    contract_model = get_contracts_provider()
    import_customer(requests_client, customer_model, consultant_model, contract_model)

def import_customer(requests_client, customer_model, consultant_model, contract_model):
    '''
        Imports customers from Close RMC. If the customer already exists
        the customer will be updated with values from Close instead.
        Customers are matched by their registration number (CVR)
        -
        :param requests_client: Request client
        :param customer_model: Customer Model
    '''
    params = {'query' : 'lead_status=(Customer)'}
    request = requests_client.get('https://api.close.com/api/v1/lead/',
            auth=(os.environ['CloseAuth'],''),
            params=params)
    response = request.json()
    for customer in response['data']:
        registration_number = None
        if 'CVR' in customer['custom']:
            if customer['custom']['CVR'].isdigit():
                registration_number = customer['custom']['CVR']
        legal_name = customer['name']

        today = datetime.datetime.today().date()

        end_of_contract = None
        if 'Contract end date' in customer['custom']:
            end_of_contract = customer['custom']['Contract end date']

        active = "N/A"
        if end_of_contract is not None:
            year,month,day = end_of_contract.split('-')
            eoc_date = datetime.date(int(year), int(month), int(day))
            active = "True" if today <= eoc_date else "False"

        current_consultants = []
        if 'Current Consultants' in customer['custom']:
            for consultant in customer['custom']['Current Consultants']:
                print(customer['custom']['Current Consultants'])
                consultant_id = next(consultant_model.email_index.query(consultant), None)
                if consultant_id is not None:
                    entry = {
                        "uuid" : consultant_id.uuid,
                        "email" : consultant
                    }
                    current_consultants.append(entry)

        exists = "N/A"
        if registration_number is not None and len(registration_number) == 8:
            exists = next(customer_model.registrationNo_index.query(registration_number), None)

        if exists is None:
            create_customer = customer_model(uuid=str(uuid.uuid4()),
            customerType = 1,
            registrationNo = registration_number,
            friendlyName = legal_name,
            active = active)

            create_customer.save()
            print("Created Customer: ", create_customer)
            if active == "True":
                create_contract = contract_model(uuid = str(uuid.uuid4()),
                active = active,
                customerId = int(registration_number),
                endDate = end_of_contract,
                consultants = json.dumps(current_consultants),
                requiredDescription = 'True',
                projects = json.dumps([]))

                create_contract.save()
                print("Created Contract: ", create_contract)
        elif exists != "N/A" and exists is not None:
            customer = customer_model.get(exists.uuid)
            customer.update(
                actions=[
                    customer_model.friendlyName.set(legal_name \
                        if legal_name is not None else "N/A"),
                    customer_model.active.set(active if active is not None else "N/A")
                ]
            )
            contract = None
            for item in contract_model.customerId_index.query(registration_number):
                if item.endDate == end_of_contract:
                    contract = item

            if contract is not None:
                contract.update(
                    actions=[
                        contract_model.consultants.set(json.dumps(current_consultants)),
                        contract_model.active.set(active if active is not None else "N/A")
                    ]
                )
                if contract.requiredDescription is None:
                    contract.update(
                        actions=[
                            contract_model.requiredDescription.set('True')
                        ]
                    )
            else:
                create_contract = contract_model(uuid = str(uuid.uuid4()),
                active = active,
                customerId = int(registration_number),
                endDate = end_of_contract,
                consultants = json.dumps(current_consultants),
                requiredDescription = "True",
                projects = json.dumps([]))

                create_contract.save()
