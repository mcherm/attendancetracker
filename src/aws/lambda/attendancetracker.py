import json
import boto3
import sys
import traceback
from collections import defaultdict
from boto3.dynamodb.conditions import Key


# global variables that will be set once per container
known_people = None # list of {"name":xxx, "teams": [xxx]} entries
displayed_team_list = None # list of teams that is always displayed, regardless of whether there are people in it



"""The list of known people hardcoded into the source. Because that's
not unreasonable at the scale I am operating now."""
HARDCODED_KNOWN_PARTICIPANTS = [
    {"participantCode":"ZNT239","name":"Andrea Williams","teams":["StormKings","#SKYE"]},
    {"participantCode":"OCJ333","name":"Christie Good","teams":["StormKings"]},
    {"participantCode":"EWP161","name":"Mary Frances Radolinski","teams":["StormKings"]},
    {"participantCode":"ZUL068","name":"Lett, Sylvia (BANK)","teams":["StormKings"]},
    {"participantCode":"RQF509","name":"Conner Hutson","teams":["StormKings"]},
    {"participantCode":"IBN631","name":"Dwight Durmon","teams":["StormKings"]},
    {"participantCode":"GEN887","name":"Nick Morgan","teams":["StormKings"]},
    {"participantCode":"HPV385","name":"Matthew Goldberg","teams":["StormKings"]},
    {"participantCode":"BJV459","name":"Chris Wagner","teams":["StormKings"]},
    {"participantCode":"BKE176","name":"Maria Beachum","teams":["StormKings"]},
    {"participantCode":"IMP911","name":"Tara Conners","teams":["StormKings"]},
    {"participantCode":"GKQ003","name":"Nita Ridge","teams":["StormKings"]},
    {"participantCode":"ZIX531","name":"Susan Law","teams":["StormKings"]},
    {"participantCode":"TJA421","name":"Martin Tamayo","teams":["Galactic Narwhals"]},
    {"participantCode":"WBK195","name":"Christophe Santini","teams":["Galactic Narwhals"]},
    {"participantCode":"MDQ896","name":"Abhishek Patel","teams":["Galactic Narwhals"]},
    {"participantCode":"EPW444","name":"Pavan Vadlamudi","teams":["Galactic Narwhals","Bagheera"]},
    {"participantCode":"HAX536","name":"Trey Duckworth","teams":["Galactic Narwhals"]},
    {"participantCode":"WTK965","name":"Tonya Garner","teams":["Galactic Narwhals","DAO Ops Automation Team","Solidaire"]},
    {"participantCode":"ZPZ254","name":"Samantha Welch","teams":["Galactic Narwhals"]},
    {"participantCode":"SCE534","name":"Scott Terry","teams":["Galactic Narwhals"]},
    {"participantCode":"CFR228","name":"Felina Dela Rosa","teams":["Elite","Radiants"]},
    {"participantCode":"EQW899","name":"VEDANT TIWARI","teams":["Elite"]},
    {"participantCode":"HEJ826","name":"JINU THOMAS","teams":["Elite"]},
    {"participantCode":"ZUS842","name":"Ramesh Poolakkil","teams":["Elite"]},
    {"participantCode":"OHI965","name":"Tyler Andrews","teams":["Elite"]},
    {"participantCode":"TKU561","name":"Caroline Sawyer","teams":["Elite"]},
    {"participantCode":"OCJ280","name":"Venugopal Vegi","teams":["Elite"]},
    {"participantCode":"RTE739","name":"Min Zhang","teams":["Elite"]},
    {"participantCode":"OMR167","name":"Bharath Kandati","teams":["Elite"]},
    {"participantCode":"WPI074","name":"Neil Parmeswar","teams":["Zion"]},
    {"participantCode":"QOI742","name":"Jennifer Davis","teams":["Zion"]},
    {"participantCode":"ABL078","name":"Nicole Lawrence-Grier","teams":["Zion"]},
    {"participantCode":"IAG226","name":"Justin Pinsky","teams":["Zero Tolerance"]},
    {"participantCode":"OJY606","name":"Austin Ward","teams":["Zero Tolerance"]},
    {"participantCode":"DOT911","name":"Asha kiran Kota","teams":["Zero Tolerance"]},
    {"participantCode":"YBL593","name":"Jinendra Pallakhe","teams":["Zero Tolerance"]},
    {"participantCode":"QPY676","name":"Sainath Gulari","teams":["Zero Tolerance"]},
    {"participantCode":"NMI137","name":"Michael Price","teams":["Zero Tolerance"]},
    {"participantCode":"CAD279","name":"Greg Robinson","teams":["Zero Tolerance"]},
    {"participantCode":"OZY257","name":"Kiran Hanumantharayappa","teams":["Zero Tolerance"]},
    {"participantCode":"VBO800","name":"Debissa Nuressa","teams":["Zero Tolerance"]},
    {"participantCode":"TNS834","name":"Jenishkumar Shah","teams":["Serenity","MindCraft"]},
    {"participantCode":"JUK220","name":"Alex Mull","teams":["Serenity","MindCraft"]},
    {"participantCode":"WHV059","name":"Adam Rudolph","teams":["Serenity"]},
    {"participantCode":"BKT193","name":"sowjanya dodda","teams":["Serenity"]},
    {"participantCode":"FGX142","name":"Stephen Douglas","teams":["Serenity"]},
    {"participantCode":"ZMK841","name":"Jimmy Antony","teams":["Serenity","MindCraft"]},
    {"participantCode":"HWR942","name":"Srinivasareddy Gogula","teams":["Serenity"]},
    {"participantCode":"SZC711","name":"Vikas Parsi","teams":["Serenity"]},
    {"participantCode":"NCQ646","name":"Steven Mettler","teams":["Radiants"]},
    {"participantCode":"FZE240","name":"Jintu Jacob","teams":["Radiants"]},
    {"participantCode":"XJB163","name":"Gouthami Mallempati","teams":["Radiants"]},
    {"participantCode":"TGQ854","name":"Mounika Kodur","teams":["Radiants"]},
    {"participantCode":"UTW628","name":"Aum Mahida","teams":["Radiants"]},
    {"participantCode":"CNR199","name":"AJITH MADHAVAN","teams":["Radiants"]},
    {"participantCode":"ZRE452","name":"Meko Hong","teams":["Radiants"]},
    {"participantCode":"YQA098","name":"Brian Bagur","teams":["#SKYE"]},
    {"participantCode":"SXI786","name":"James Evans","teams":["#SKYE"]},
    {"participantCode":"QTD274","name":"Billy Hall","teams":["#SKYE","Lending 3","Torchwood","Strangertech"]},
    {"participantCode":"VUS891","name":"Dinesh Karunakaran","teams":["#SKYE"]},
    {"participantCode":"INX212","name":"Clark Plaisance","teams":["#SKYE"]},
    {"participantCode":"LMD800","name":"Anita Brown","teams":["#SKYE"]},
    {"participantCode":"RVS083","name":"Brian Nguyen","teams":["Bagheera"]},
    {"participantCode":"QCZ838","name":"Desha Corey","teams":["Bagheera"]},
    {"participantCode":"TFQ390","name":"Mamatha Aerolla","teams":["Bagheera"]},
    {"participantCode":"YRD751","name":"Vijay Mara","teams":["Bagheera"]},
    {"participantCode":"WXO639","name":"Wesley Orbin","teams":["Bagheera"]},
    {"participantCode":"OLV406","name":"Caroli Beausoleil","teams":["Bagheera","Shadow Manatees"]},
    {"participantCode":"EHT092","name":"Hajarathaiah Podalakuru","teams":["Bagheera"]},
    {"participantCode":"RIN756","name":"Jesse Gutierrez","teams":["Bagheera"]},
    {"participantCode":"SSK617","name":"Ian Hazlett","teams":["Quantico"]},
    {"participantCode":"ZFX497","name":"Haseeb Ahamed Naseem","teams":["Quantico"]},
    {"participantCode":"UKC733","name":"Akshay Sharma","teams":["Quantico"]},
    {"participantCode":"DLU167","name":"Sajal Gahoi","teams":["Quantico"]},
    {"participantCode":"FIE718","name":"Tyler Grant","teams":["Quantico","Langley"]},
    {"participantCode":"TJK208","name":"SHARMARKE ADEN","teams":["Quantico"]},
    {"participantCode":"BGO494","name":"Shiva Gannavaram","teams":["Quantico","Langley"]},
    {"participantCode":"MUQ445","name":"Prakash Vaideeswaran","teams":["Secret Service","TopCoin"]},
    {"participantCode":"CID549","name":"Lateef Mohammad","teams":["Secret Service"]},
    {"participantCode":"SLU080","name":"Ramesh Babu Tirumalasetti","teams":["Secret Service","TopCoin"]},
    {"participantCode":"UXR753","name":"Suvedhan Jayaraman","teams":["Secret Service"]},
    {"participantCode":"MTP926","name":"Arian Azin","teams":["Secret Service"]},
    {"participantCode":"KXS661","name":"Connor Herr","teams":["Secret Service"]},
    {"participantCode":"WSF540","name":"Zachary Manno","teams":["Secret Service"]},
    {"participantCode":"TKA685","name":"John Grisamore","teams":["Torchwood"]},
    {"participantCode":"CYX555","name":"DOLLY RAJDEV","teams":["Torchwood","Strangertech"]},
    {"participantCode":"DCW207","name":"Amit Rawat","teams":["Torchwood"]},
    {"participantCode":"KIV948","name":"BHAVANA TRIPURANENI","teams":["Torchwood"]},
    {"participantCode":"NZO859","name":"Brian Crawford","teams":["Torchwood"]},
    {"participantCode":"BHS284","name":"Elangovan Kuppusamy","teams":["Torchwood"]},
    {"participantCode":"CWI325","name":"Christy Templet","teams":["Torchwood"]},
    {"participantCode":"GCY698","name":"Raghavendra Comaleshwarampet","teams":["Torchwood"]},
    {"participantCode":"EHB867","name":"Maran Chandrasekaran","teams":["Torchwood"]},
    {"participantCode":"TTH577","name":"Tapiwa Maruni","teams":["Strangertech"]},
    {"participantCode":"ECY854","name":"Joe Ann Patterson","teams":["Strangertech"]},
    {"participantCode":"LTN501","name":"Balaraju Gujjari","teams":["Strangertech"]},
    {"participantCode":"XLC009","name":"Mallikarjun Mallesh","teams":["Strangertech"]},
    {"participantCode":"EMU761","name":"manoj kumar","teams":["Strangertech"]},
    {"participantCode":"CHO215","name":"Maghan Gautney","teams":["Strangertech"]},
    {"participantCode":"ZJR187","name":"VIKRAM TRIPURANENI","teams":["Strangertech"]},
    {"participantCode":"HFN884","name":"Troy Yeager","teams":["SB Digital Bank Program Team"]},
    {"participantCode":"EVN068","name":"Jiji Cherian","teams":["SB Digital Bank Program Team"]},
    {"participantCode":"RDG959","name":"Michael Chermside","teams":["SB Digital Bank Program Team"]},
    {"participantCode":"IHR057","name":"Subramanyam Jayaraman","teams":["SB Digital Bank Program Team"]},
    {"participantCode":"NJF132","name":"Bryan Deitrich","teams":["SB Digital Bank Program Team"]},
    {"participantCode":"VIJ361","name":"Mahalakshmi Venkataraman","teams":["SB Digital Bank Program Team"]},
    {"participantCode":"DZM430","name":"David Weaver","teams":["SB Digital Bank Program Team"]},
    {"participantCode":"UWT275","name":"Laura Cherry","teams":["Three Wolf Moon"]},
    {"participantCode":"FJL161","name":"Jayakrishnan Sreedharan","teams":["Three Wolf Moon"]},
    {"participantCode":"FEE872","name":"VIVEK SHANKAR","teams":["Three Wolf Moon"]},
    {"participantCode":"DIH765","name":"William Sanders","teams":["Three Wolf Moon"]},
    {"participantCode":"WPW296","name":"Faye Dobler","teams":["Three Wolf Moon","Shadow Manatees"]},
    {"participantCode":"ZGM815","name":"Rupam Gupta","teams":["Three Wolf Moon"]},
    {"participantCode":"DYX339","name":"Shamjith Kottath","teams":["TopCoin"]},
    {"participantCode":"YAP314","name":"Maeve McCoy","teams":["TopCoin"]},
    {"participantCode":"VNG213","name":"Gregory Isaac Patselas","teams":["TopCoin"]},
    {"participantCode":"HTL545","name":"PRANAV KANUKOLLU","teams":["TopCoin"]},
    {"participantCode":"CZI240","name":"Sreejith Chandran","teams":["TopCoin"]},
    {"participantCode":"PPC433","name":"David Yu","teams":["FORCE SQUAD"]},
    {"participantCode":"PKM111","name":"HariBabu Matta","teams":["FORCE SQUAD"]},
    {"participantCode":"WBI189","name":"ANKUR TYAGI","teams":["FORCE SQUAD"]},
    {"participantCode":"YZO998","name":"Ashwath Kumar Kannan","teams":["FORCE SQUAD","Force Ninja's"]},
    {"participantCode":"ZFK681","name":"TONY GAO","teams":["FORCE SQUAD"]},
    {"participantCode":"FPI114","name":"Christi Cruz","teams":["FORCE SQUAD"]},
    {"participantCode":"QLJ199","name":"William Jones","teams":["FORCE SQUAD"]},
    {"participantCode":"KER450","name":"Ashish Shishodiya","teams":["FORCE SQUAD"]},
    {"participantCode":"PTM259","name":"Mohammad Thajuddin","teams":["Force Ninja's"]},
    {"participantCode":"BJM808","name":"Cameron Stinson","teams":["Force Ninja's"]},
    {"participantCode":"NCD505","name":"Srividya Murali","teams":["Force Ninja's"]},
    {"participantCode":"HBQ598","name":"SHAKHA GUPTA","teams":["Force Ninja's"]},
    {"participantCode":"HMD871","name":"Wilson Yu","teams":["Small Business & Canada - Continuous Improvement"]},
    {"participantCode":"XTS595","name":"Wendy Coulstock","teams":["Small Business & Canada - Continuous Improvement"]},
    {"participantCode":"ZQJ572","name":"Joan Gammon","teams":["Small Business & Canada - Continuous Improvement"]},
    {"participantCode":"NMR202","name":"Jeffrey Kopf","teams":["Small Business & Canada - Continuous Improvement"]},
    {"participantCode":"JTZ575","name":"Scott Weiner","teams":["Small Business & Canada - Continuous Improvement"]},
    {"participantCode":"PNC418","name":"Natalie Divney","teams":["Small Business & Canada - Continuous Improvement"]},
    {"participantCode":"NPI266","name":"William Barbery","teams":["Small Business & Canada - Continuous Improvement"]},
    {"participantCode":"EXJ490","name":"Diane Weaver","teams":["Small Business & Canada - Continuous Improvement"]},
    {"participantCode":"LFN231","name":"Robert layton","teams":["Small Business & Canada - Continuous Improvement"]},
    {"participantCode":"KVX260","name":"Derek Huether","teams":["Small Business & Canada - Continuous Improvement"]},
    {"participantCode":"EYY445","name":"Kavitha Veluri","teams":["Shadow Manatees"]},
    {"participantCode":"UIF478","name":"Janak Malla","teams":["Shadow Manatees"]},
    {"participantCode":"CNG669","name":"Rajesh Sakhare","teams":["Shadow Manatees"]},
    {"participantCode":"ITC554","name":"Shweta Javagi Surender","teams":["Shadow Manatees"]},
    {"participantCode":"HZQ893","name":"Benjamin Liang","teams":["Shadow Manatees"]},
    {"participantCode":"WCD112","name":"Jacob Gunter","teams":["Shadow Manatees"]},
    {"participantCode":"KRJ476","name":"Andrew Hale","teams":["Shadow Manatees"]},
    {"participantCode":"KDD397","name":"Michelle Chen","teams":["Shadow Manatees"]},
    {"participantCode":"NXK335","name":"Bhavikkumar Desai","teams":["DAO Ops Automation Team"]},
    {"participantCode":"UXO146","name":"Nafiz Mohammad","teams":["DAO Ops Automation Team","Money Magicians"]},
    {"participantCode":"LVA833","name":"Chandramohan Kirushnamoorthi","teams":["DAO Ops Automation Team"]},
    {"participantCode":"SWX334","name":"Vishal Roy","teams":["MindCraft"]},
    {"participantCode":"IFD721","name":"Shakti Rawat","teams":["MindCraft"]},
    {"participantCode":"PHN128","name":"Suresh Kulambi Basavalingappa","teams":["MindCraft"]},
    {"participantCode":"TGB495","name":"Imran Khan","teams":["Money Magicians"]},
    {"participantCode":"IND318","name":"Basil Kerai","teams":["Money Magicians"]},
    {"participantCode":"XNL104","name":"Dianna Samuelson","teams":["Money Magicians"]},
    {"participantCode":"YEW622","name":"Yimin Lu","teams":["Money Magicians"]},
    {"participantCode":"LUP090","name":"Ralph Boyd IV","teams":["Money Magicians"]},
    {"participantCode":"LBG397","name":"Prasenjit Kundu","teams":["Money Magicians"]},
    {"participantCode":"ANY745","name":"Vishnuvardhan Devi","teams":["Langley"]},
    {"participantCode":"IQP019","name":"Nikita Dinavahi","teams":["Langley"]},
    {"participantCode":"NQA307","name":"Haojiong Liu","teams":["Langley"]},
    {"participantCode":"TSO405","name":"Kiel Lew","teams":["Langley"]},
    {"participantCode":"RJX835","name":"SANJAY NAIK","teams":["Sleek Squad"]},
    {"participantCode":"CBU314","name":"ALI ISHAQUE","teams":["Sleek Squad"]},
    {"participantCode":"APS187","name":"Shenchu NMN Zhang","teams":["Sleek Squad"]},
    {"participantCode":"SPP713","name":"Lauren Hill","teams":["Sleek Squad"]},
    {"participantCode":"BBC446","name":"Arleta Brodell","teams":["Sleek Squad"]},
    {"participantCode":"AHO135","name":"Scott Fraser","teams":["Sleek Squad"]},
    {"participantCode":"DPS313","name":"Veeranna, Nagendra (CONT)","teams":["Sleek Squad"]},
    {"participantCode":"XZM421","name":"Jeffrey Michael Bolden","teams":["Customer Core Wipro"]},
    {"participantCode":"IDV814","name":"Weller Eric","teams":["Solidaire"]},
    {"participantCode":"YDE698","name":"Thomas Evan Webb","teams":["Solidaire"]},
    {"participantCode":"THV211","name":"Jeffrey John Hertel","teams":["Solidaire"]},
    {"participantCode":"INR594","name":"Arvind Tangirala","teams":["SBB Architecture"]},
    {"participantCode":"WES971","name":"DIANHAI DU","teams":["SBB Architecture"]},
]

HARDCODED_TEAMS_TO_HIDE = [
    "SB Digital Bank Program Team",
    "SB Lending Program Team",
    "SBB Fraud_Two",
    "Small Business & Canada - Continuous Improvement",
    "Solidaire",
    "Zero Tolerance_Two",
    "Zion",
    ]

def load_known_people():
    """Invoked to set the global variables known_people and teams. It returns
    them as a tuple."""
    # dynamodb = boto3.resource('dynamodb')
    # participants_table = dynamodb.Table('attendancetracker-participants')
    # scan_result = participants_table.scan(
    #     Select="ALL_ATTRIBUTES",
    #     ConsistentRead=False
    # )
    # participant_items = scan_result["Items"]
    participant_items = HARDCODED_KNOWN_PARTICIPANTS
    known_people = {}
    team_set = set()
    for participant_item in participant_items:
        participant_code = participant_item["participantCode"]
        participant_name = participant_item["name"]
        participant_teams = participant_item["teams"]
        known_people[participant_code] = {
            "name": participant_name,
            "teams": participant_teams
        }
        team_set.update(participant_teams)
    displayed_team_list = list(sorted(x for x in team_set if x not in HARDCODED_TEAMS_TO_HIDE))
    return known_people, displayed_team_list



def process_request(event, context):
    """This is called by the lambda_handler. It is permitted to raise
    exceptions."""
    eventCode = event["pathParameters"]["eventCode"]

    dynamodb = boto3.resource('dynamodb')
    signins_table = dynamodb.Table('attendancetracker-signins')
    query_result = signins_table.query(
        KeyConditionExpression=Key("eventCode").eq(eventCode),
        Select="ALL_ATTRIBUTES",
        ConsistentRead=False
    )
    signins = query_result["Items"]

    global known_people
    global displayed_team_list
    if known_people is None:
        print("Loading participants") # leave this logged - should happen once per container
        known_people, displayed_team_list = load_known_people()

    participant_names = []
    team_participation = defaultdict(list)
    # populate empty values for all displayed teams
    for team in displayed_team_list:
        team_participation[team] = []
    for signin in signins:
        participant_code = signin["participantCode"]
        if participant_code in known_people:
            # known participant
            known_person = known_people[participant_code]
            name = known_person["name"]
            teams = known_person["teams"]
        else:
            # Unknown participants
            name = participant_code
            null_team_name = "Unknown"
            teams = [null_team_name]
            if null_team_name not in team_participation:
                team_participation[null_team_name] = []
        participant_names.append(name)
        for team in teams:
            team_participation[team].append(name)

    response_body = {
        "signins": signins,
        "teams": team_participation,
        "participant_names": participant_names
    }

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(response_body)
    }


def lambda_handler(event, context):
    try:
        result = process_request(event, context)
    except Exception as err:
        traceback.print_exc()
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": f'{{"error":"{sys.exc_info()[0].__name__}","message":"{sys.exc_info()[1]}"}}'
        }
    else:
        return result
