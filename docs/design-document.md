# Personal Learning Record Store (PLRS) BB – Design Document

Personal Learning Record Store (PLRS) service is a type of cloud-based service that allows individuals to store and manage their own learning records in a central location. A PLRS will allow individuals to easily access, download, and reuse their personal learning data, which is a key aspect of data portability under the GDPR. It also helps the data controller to comply with GDPR regulation. PLRS will allow individuals to keep track of their learning activities, achievements, and progress, and to share this information with others if, or when, they choose to.

While a typical [Learning Record Store (LRS)](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-About.md#part-one-about-the-experience-api) is owned by the organizations providing the training to the learner, a PLRS is owned directly by the learner itself.

A personal LRS can be considered as a "personal cloud" service, as it allows individuals to store and access their learning records from any device with internet access. It also provides a level of control, security and privacy as the data is owned and controlled by the individual. Personal LRS can also allow for greater interoperability with other systems or applications by providing a standardized way of storing and sharing learning records.

Please note that the following visuals are intended as projections only. UX/UI work will be carried out later in the process.

![Cozy store](https://github.com/Prometheus-X-association/plrs/assets/129832540/54e17b27-27e3-4791-be1f-f3ea78e188e2)

![Cosy store - PLRS](https://github.com/Prometheus-X-association/plrs/assets/129832540/89f5b741-6d72-4368-b04c-cbd621b1bdd3)

![PLRS](https://github.com/Prometheus-X-association/plrs/assets/129832540/23e04cd1-59d8-40d4-a3ce-2bdcd615be96)


## Technical usage scenarios & Features

**Key functionalities:**

- export learning traces from LMS to PLRS (in LMS frontend)

- import learning traces from LMS to PLRS (in PLRS frontend)

- visualize learning traces in PLRS

- synchronize PLRS data with external LRS (regular push)

- local access to data for edge computing

**Value-added:**

- lifelong availability of my learning data

- better learning path/career analysis

- edge computing

### Features/main functionalities

**Features**: 

- **Export learning traces from LMS to PLRS (in LMS frontend)** 
Depending on the LMS, a gateway will be created. It can take the form of a button. When users click on it, they send their personal data to the PLRS. 
Knowing that the PLRS only accepts xAPI format, if the data from the LMS does not have this format, the first call will be made to the LRC. 

- **Import learning traces from LMS to PLRS (in PLRS frontend)** 
If the LMS the learner is using doesn't have this direct export to PLRS button, then they can choose to export their dataset from the LMS and then import it into PLRS. 

- **Visualize learning traces in PLRS** 
The aim is not to have a complete visualization of learning traces. It just needs to display a limited amount of information in the dashboard, such as: number of traces per day, certification in progress, certification acquired, etc. (tbd). \
For a complete visualization, the PLRS can be connected to another application dedicated to this purpose. 

- **Synchronize PLRS data with external LRS** 
Students can permanently (or not) share their learning traces with an external LRS. Synchronization is a regular push operation. Whether it's to justify their progress to a school or to their employer, users are in control of their data. These data exchanges are in xAPI format. 


- **Local access to data for decentralized AI training** 
This makes it possible to run computation on the data locally (within the PLRS) and only return the result. This way learner data do not exit their PLRS and limit privacy issues associated with sharing data externally.

### Technical usage scenarios

A student can use their Personal Learning Record Store (PLRS) in a variety of ways to track their learning activities and progress. Here is an example of how a student might use their PLRS:

1. Tracking learning activities: The student can use their PLRS to log their learning activities, such as classes, workshops, and self-study sessions. They can also include information about the topics covered and the resources used.

2. Recording achievements: The student can use their PLRS to record achievements such as completing a course, passing an exam, or receiving a certification. This information can be used to demonstrate their learning progress to others.

3. Sharing with others: If desired, the student can share the learning data in their PLRS with others, such as potential employers, educational institutions, or learning coaches. This allows them to demonstrate their learning progress and achievements to others.

4. Keeping a record of the learning journey: The student can use the PLRS to keep a record of their learning journey, which can be useful for planning future learning and career goals.

5. Providing evidence for micro-credentials or badges earned: The student can use the PLRS to store and provide evidence for any micro-credentials or badges earned.

6. Providing data for analytics: The student can use their PLRS to provide data for analytics, such as identifying areas where they need improvement, tracking their progress over time, and measuring the impact of different learning activities.

The PLRS is beneficial for training organizations:

1. Ensure training progress: The student can share his or her credentials and progress on a permanent basis.

2. Detecting trouble spots: Thanks to sharing, the organization will have more learning traces, making it possible to detect learner difficulties, especially those recorded before the student joined the current training organization.

The PLRS is beneficial for future employers:

1. Check skills held: Locally shared traces enable the future employer to ascertain the skills of the individual. This can have a positive impact on the person's employment, as their skills are verified and not just a line on their CV.

2. Don't waste time on profiles that don't match: The future employer can easily detect whether the person's skills are in line with those required for a job. This way, the employer and the individual don't waste time when there's no match.

## Requirements

| Requirement ID | Short description | BB input format | BB output format | Any other constraints | Verified by scenario | Requirement type |
|---|---|---|---|---|---|---|
| BB-REQ_ID__1 | PLRS must request building block consent via the Prometheus-X Dataspace Connector | API call | API response |  |  |  |
| BB-REQ_ID__1.1 | Individuals must consent to the export, import, and use of their data in PLRS. | API call | API response | If the answer is no, the data cannot be used, nor transferred into or from the PLRS. If the answer is yer, the data can be used, and transferred into or from the PLRS. | BB-SC-PLRS-01 | DEP |
| BB-REQ_ID__1.2 | Consent must be asked and verified in less than 30s | API call | API response |  | BB-SC-PLRS-02 | PERF |
| BB-REQ_ID__2 | PLRS must request contracts from the building block consent via the Prometheus-X Dataspace Connector | API call | API response |  |  |  |
| BB-REQ_ID__2.1 | The PLRS must check with the contract manager through the Dataspace connector if a contract for the corresponding organization exists | API call | API response | If the answer is no, the data cannot be accessed, nor transferred into or from the PLRS. If the answer is yer, the data can be accessed, and transferred into or from the PLRS. | BB-SC-PLRS-03 | DEP |
| BB-REQ_ID__2.2 | Contract must be asked and verified in less than 30s | API call | API response |  | BB-SC-PLRS-04 | PERF |
| BB-REQ_ID__3 | PLRS must connect with BB Consent/contracts negotiating agent (EDGE-Skill) |  |  |  |  |  |
| BB-REQ_ID__3.1 | BB must send the individual's consent profile when the PLRS asks to adjust what and when they are tracked: all-time connection, only on weekends, certain keywords, etc. | API call | consent profile | Request consent 1 time, then update if the profile is modified in the corresponding building bloc. Could be asynchronous | BB-SC-PLRS-05 | DEP |
| BB-REQ_ID__3.2 | BB must update the individual's consent profile to PLRS when there are changes | consent profile | / | update if the profile is modified in the corresponding building bloc. Could be asynchronous | BB-SC-PLRS-06 | DEP |
| BB-REQ_ID__4 | PLRS should connect with BB Data veracity assurance (EDGE-Skill) | API call | API response |  |  |  |
| BB-REQ_ID__4.1 | BB Data veracity assurance should check dataset homogeneity and detail | xAPI (DASES) dataset | response |  | BB-SC-PLRS-07 | FUN |
| BB-REQ_ID__5 | PLRS should connect with BB Decentralized AI training (EDGE-Skill) |  |  |  |  |  |
| BB-REQ_ID__5.1 | PLRS should be able to run algorithm shared by BB Decentralized AI training, locally on the data in the PLRS | API interaction | API interaction | Data transfer via xAPI. Could be asynchronous | BB-SC-PLRS-08 | FUN |
| BB-REQ_ID__5.2 | Running the algorithm must be done in less than 2 min | API call | API response |  | BB-SC-PLRS-09 | PERF |

## Integrations

### Direct Integrations with Other BBs

| Category                                    | Why?                                      | How?                                                                     |
|---------------------------------------------|-------------------------------------------|--------------------------------------------------------------------------|
| Interact with Decentralized AI training     | train AI model                            | send anonymized (or not) data to train AI models                         |
| Interact with Data veracity assurance       | Ensure that data exploitation is feasible<br>Ensure data consistency | Send access to dataset                                                  |
| Interact with consent/contract              | Transparency on data transfer             | Identify data import period (date, time, week)<br>Identify data export period (date, time, week, organization) |
| Interact with Distributed data visualization| Visualize the learner's skills            | Send dataset in xAPI format<br>Asynchronous                             |
| Interact with LRC                           | Harmonize data in the PLRS in xAPI        | Convert any dataset to xAPI format                                       |


### Integrations via Connector

| Category                       | Why?                                                       | What?                                                                                                   |
|--------------------------------|------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Connection with connector      | Simplify communication between the PLRS and PTX CCs       |                                                                                                        |
| Connection with contract       | Contract between PLRS and the LMS authorizing export of user data | Obtain the organization's agreement to export user data.<br>Identify the data standard to be transferred. |
| Connection with consent        | User consent to export/import his data                    | Obtain the user's consent to export data.<br>Obtain consent to import data.<br>Obtain person's agreement to share data with selected organizations/persons.<br>Obtain the person's agreement to use his data to improve AI.<br>Obtain consent to analyze data. |
| Connection with identity       | Enable PLRS to use users' identities to display metadata with others | Use the user's first and last name.<br>Use the user's professional background.<br>Use the user's educational background. |



## Relevant Standards

### Data Format Standards

**Data format**

- The data produced and/or consumed are learning records. These are logs of learning activity done by a user.

- There are several standard formats for learning records (SCORM, xAPI, cmi5, IMS caliper)
  
- The consensus among experts is that xAPI is the most promising standard for describing learning records.

- Inokufu have published on Prometheus-X's github a state of the art study about learning records interoperability in 2023 (see [here](https://github.com/Prometheus-X-association/learning-records-interoperability-2023)). This study describes the various formats and explains why “we" have selected xAPI as the defacto format for learning records for DASES (Dataspace of Education & Skills).
    - In summary, xAPI have been chosen over SCORM, IMS Caliper, and cmi5 for its unparalleled flexibility and comprehensive data tracking capabilities.
    - While SCORM has served the e-learning community well, its limitations in handling offline learning, detailed data reporting, and informal learning experiences became apparent. SCORM’s inability to adapt to the rapidly evolving tech world, including mobile devices and cloud-based technologies, hindered its efficacy.
    - IMS Caliper, though robust in tracking web-based digital learning environments, falls short in its versatility compared to xAPI. xAPI can track a wide range of learning experiences across multiple platforms, including mobile, games, simulations, and offline interactions. This makes it a far more adaptable solution for modern learning environments.
    - Although cmi5 effectively bridges SCORM and xAPI by combining xAPI's tracking capabilities with SCORM's structured control, it still lacks the full flexibility provided by xAPI. Additionally, xAPI presents better compatibility conditions with different LMS and authoring tools compared to cmi5, thereby fostering greater interoperability within the data space.
    - The true strength of xAPI lies in its "extensions" attribute, allowing the capture of unique or granular details about any learning experience. This feature ensures that xAPI can be tailored to meet the specific needs of any organization, providing detailed and diverse data without being constrained by predefined parameters.
    - In essence, xAPI's ability to provide a shared data format that facilitates easy data transfer between systems while enabling highly relevant and specific tracking aspects makes it the optimal choice for our evolving educational needs.

- In xAPI, each learning record is a json statement. This json contains several parts: actor, verb, object, result, context, timestamp.

- The most critical personal data are in general in the actor part. According to xAPI, one can use first name, last name or email as the actor identifier. However, in our case we always recommend using uuid to identify actors. This way our learning records are pseudonymized by default. As this won’t always be the case with other organizations connected to the dataspace.

- If shared datasets are not in xAPI format, there is a BB ([Learning Records Converter](https://github.com/Prometheus-X-association/learning-records-converter)) that is part of the PTX dataspace that allows conversion to the chosen format for exchanges within the dataspace.

### Mapping to Data Space Reference Architecture Models


```mermaid

block-beta

columns 7

LMSExport:1 
LMS_PDC:1 
PLRS_PDC:1

PLRS:1

PLRS_PDC_:1

block:group3
columns 1
CC_PDC DVA_PDC DAI_PDC
end

block:group4
columns 1
ConsentContracts DataVeracityAssurance DecentralizedAItraining
end

classDef colorA fill:#D22FF7,color:#fff
classDef colorEx fill:#01D1D1,color:#fff
classDef colorED fill:#6E7176,color:#fff
class LMSExport colorEx
class PLRS colorED
class EdgeComputing colorED
class ConsentContracts colorED
class DataVeracityAssurance colorED
class DecentralizedAItraining colorED
class PLRS_PDC colorA
class LMS_PDC colorA
class PLRS_PDC_ colorA
class CC_PDC colorA
class DVA_PDC colorA
class DAI_PDC colorA
```
The blocks depicted in the architecture graphic represent hypothetical functions, as their development has not yet been completed. However, we aim to communicate with the "consent contract" to transparently track users. This means that users will be able to personalize various parameters, such as the days of the week and hours they choose to be tracked. By prioritizing user control and consent, we aim to build trust and adhere to privacy regulations, ensuring users have a clear understanding and authority over their tracking preferences.

PDC : Prometheus-X Dataspace Connector

## Input / Output Data

Input and output data are in the same format: xAPI.

Example of Becomino learning traces for an access : 
```json
{
  "stored": "2024-03-11T14:17:43.686Z",
  "priority": "MEDIUM",
  "active": true,
  "completedForwardingQueue": [],
  "failedForwardingLog": [],
  "client": "626a34fe1deb08f53ac12609",
  "lrs_id": "626a34fe1deb08d43dc12608",
  "completedQueues": [
    "STATEMENT_QUERYBUILDERCACHE_QUEUE",
    "STATEMENT_PERSON_QUEUE",
    "STATEMENT_FORWARDING_QUEUE"
  ],
  "activities": [
    "https://becomino.com/category/competences-bureautiques"
  ],
  "hash": "2b898680c9870ee54d8d260b75eb45d38fbb6c24",
  "agents": [
    "https://becomino.com/users|1710166580617x845375926584167200"
  ],
  "statement": {
    "authority": {
      "objectType": "Agent",
      "name": "Becomino",
      "mbox": "mailto:contact@becomino.com"
    },
    "stored": "2024-03-11T14:17:43.686Z",
    "context": {
      "contextActivities": {
        "parent": [
          {
            "id": "https://becomino.com/home",
            "objectType": "Activity"
          }
        ],
        "category": [
          {
            "id": "https://becomino.com/category/404",
            "objectType": "Activity"
          }
        ],
        "grouping": [
          {
            "id": "https://becomino.com/board/404",
            "objectType": "Activity"
          }
        ]
      },
      "language": "fr"
    },
    "actor": {
      "account": {
        "homePage": "https://becomino.com/users",
        "name": "1710166580617x845375926584167200"
      },
      "objectType": "Agent"
    },
    "timestamp": "2024-03-11T14:17:32.814Z",
    "version": "1.0.0",
    "id": "8f5e30f6-312e-4ec6-bc60-a37bcb1811ec",
    "verb": {
      "id": "https://w3id.org/xapi/netc/verbs/accessed",
      "display": {
        "en-US": "accessed"
      }
    },
    "object": {
      "id": "https://becomino.com/category/competences-bureautiques",
      "definition": {
        "name": {
          "fr": "Compétences bureautiques"
        },
        "description": {
          "fr": ""
        },
        "type": "http://adlnet.gov/expapi/activities/link"
      },
      "objectType": "Activity"
    }
  },
  "hasGeneratedId": true,
  "deadForwardingQueue": [],
  "voided": false,
  "verbs": [
    "https://w3id.org/xapi/netc/verbs/accessed"
  ],
  "personaIdentifier": "65ef1288fff35065a8f02d8c",
  "processingQueues": [],
  "person": {
    "_id": "65ef128899ffae0133166652",
    "display": "1710166580617x845375926584167200 - https://becomino.com/users (xAPI Account)"
  },
  "timestamp": "2024-03-11T14:17:32.814Z",
  "relatedActivities": [
    "https://becomino.com/category/competences-bureautiques",
    "https://becomino.com/home",
    "https://becomino.com/board/404",
    "https://becomino.com/category/404"
  ],
  "relatedAgents": [
    "https://becomino.com/users|1710166580617x845375926584167200",
    "mailto:contact@becomino.com"
  ],
  "organisation": "626a340cccbcc9000aff1421",
  "_id": "65ef1287c56582001cca4966",
  "registrations": [],
  "pendingForwardingQueue": []
}
```

Example of Becomino learning traces for an opening : 
```json
{
  "stored": "2024-03-11T14:03:53.853Z",
  "priority": "MEDIUM",
  "active": true,
  "completedForwardingQueue": [],
  "failedForwardingLog": [],
  "client": "626a34fe1deb08f53ac12609",
  "lrs_id": "626a34fe1deb08d43dc12608",
  "completedQueues": [
    "STATEMENT_QUERYBUILDERCACHE_QUEUE",
    "STATEMENT_PERSON_QUEUE",
    "STATEMENT_FORWARDING_QUEUE"
  ],
  "activities": [
    "https://www.youtube.com/watch?v=mBB_4io4t7w"
  ],
  "hash": "9c1dfe88035942439811946b7be0045c676b2de0",
  "agents": [
    "https://becomino.com/users|1710165537783x892345052938840600"
  ],
  "statement": {
    "authority": {
      "objectType": "Agent",
      "name": "Becomino",
      "mbox": "mailto:contact@becomino.com"
    },
    "stored": "2024-03-11T14:03:53.853Z",
    "context": {
      "contextActivities": {
        "parent": [
          {
            "id": "https://becomino.com/board/devenir-pro-immobilier-1638124052784x348049108536401000",
            "objectType": "Activity"
          }
        ],
        "category": [
          {
            "id": "https://becomino.com/category/vente",
            "objectType": "Activity"
          }
        ],
        "grouping": [
          {
            "id": "https://becomino.com/board/devenir-pro-immobilier",
            "objectType": "Activity"
          }
        ]
      },
      "language": "fr",
      "extensions": {
        "http://schema.inokufu.com/becomino/board": {
          "id": "https://becomino.com/board/devenir-pro-immobilier",
          "name": {
            "fr": "Devenir Pro en Transactions Immobilières"
          }
        }
      }
    },
    "actor": {
      "account": {
        "homePage": "https://becomino.com/users",
        "name": "1710165537783x892345052938840600"
      },
      "objectType": "Agent"
    },
    "timestamp": "2024-03-11T14:03:42.852Z",
    "version": "1.0.0",
    "id": "24215902-50d4-4a5a-8cf7-aa6df42ad394",
    "verb": {
      "id": "https://w3id.org/xapi/netc/verbs/opened",
      "display": {
        "en-US": "opened"
      }
    },
    "object": {
      "id": "https://www.youtube.com/watch?v=mBB_4io4t7w",
      "definition": {
        "name": {
          "fr": "Agent immobilier - Le métier"
        },
        "description": {
          "fr": "bonjour à tous je suis rom un quartier de la société romain quartier formation spécialisée en accompagnement et coaching immobilier j'ai conçu le test agent immobilier pour vous aider à prouver vos compétences et vous faire remarquer par des employeurs notre métier évolue enfin j'ai envie de vous di..."
        },
        "type": "http://adlnet.gov/expapi/activities/link",
        "extensions": {
          "http://schema.inokufu.com/learning-object/type": "Video",
          "http://schema.inokufu.com/learning-object/bloom": "discover",
          "http://schema.inokufu.com/learning-object/provider": "YouTube",
          "http://schema.inokufu.com/learning-object/picture": "https://i.ytimg.com/vi/mBB_4io4t7w/maxresdefault.jpg"
        }
      },
      "objectType": "Activity"
    }
  },
  "hasGeneratedId": true,
  "deadForwardingQueue": [],
  "voided": false,
  "verbs": [
    "https://w3id.org/xapi/netc/verbs/opened"
  ],
  "personaIdentifier": "65ef0e8cfff35065a8efaec2",
  "processingQueues": [],
  "person": {
    "_id": "65ef0e8c99ffaefc9516664e",
    "display": "1710165537783x892345052938840600 - https://becomino.com/users (xAPI Account)"
  },
  "__v": 1,
  "timestamp": "2024-03-11T14:03:42.852Z",
  "relatedActivities": [
    "https://www.youtube.com/watch?v=mBB_4io4t7w",
    "https://becomino.com/board/devenir-pro-immobilier-1638124052784x348049108536401000",
    "https://becomino.com/board/devenir-pro-immobilier",
    "https://becomino.com/category/vente"
  ],
  "relatedAgents": [
    "https://becomino.com/users|1710165537783x892345052938840600",
    "mailto:contact@becomino.com"
  ],
  "organisation": "626a340cccbcc9000aff1421",
  "_id": "65ef0f49c56582001cca4930",
  "registrations": [],
  "pendingForwardingQueue": []
}
```

Example of Becomino learning traces for a search : 
```json
{
  "stored": "2024-03-11T14:03:18.048Z",
  "priority": "MEDIUM",
  "active": true,
  "completedForwardingQueue": [],
  "failedForwardingLog": [],
  "client": "626a34fe1deb08f53ac12609",
  "lrs_id": "626a34fe1deb08d43dc12608",
  "completedQueues": [
    "STATEMENT_QUERYBUILDERCACHE_QUEUE",
    "STATEMENT_PERSON_QUEUE",
    "STATEMENT_FORWARDING_QUEUE"
  ],
  "activities": [
    "https://becomino.com/search/autocomplete%3Dvente"
  ],
  "hash": "c767c476e1ceec741589d207eb20c88a444f77a2",
  "agents": [
    "https://becomino.com/users|1710165537783x892345052938840600"
  ],
  "statement": {
    "authority": {
      "objectType": "Agent",
      "name": "Becomino",
      "mbox": "mailto:contact@becomino.com"
    },
    "stored": "2024-03-11T14:03:18.048Z",
    "context": {
      "contextActivities": {
        "parent": [
          {
            "id": "https://becomino.com/account",
            "objectType": "Activity"
          }
        ],
        "category": [
          {
            "id": "https://becomino.com/category/404",
            "objectType": "Activity"
          }
        ],
        "grouping": [
          {
            "id": "https://becomino.com/board/404",
            "objectType": "Activity"
          }
        ]
      },
      "language": "fr"
    },
    "actor": {
      "account": {
        "homePage": "https://becomino.com/users",
        "name": "1710165537783x892345052938840600"
      },
      "objectType": "Agent"
    },
    "timestamp": "2024-03-11T14:03:06.821Z",
    "version": "1.0.0",
    "id": "773aa025-fa60-4dab-97f7-515efdf1e2cb",
    "verb": {
      "id": "https://w3id.org/xapi/acrossx/verbs/searched",
      "display": {
        "en-US": "searched"
      }
    },
    "object": {
      "id": "https://becomino.com/search/autocomplete%3Dvente",
      "definition": {
        "name": {
          "fr": "autocomplete=vente"
        },
        "description": {
          "fr": ""
        }
      },
      "objectType": "Activity"
    }
  },
  "hasGeneratedId": true,
  "deadForwardingQueue": [],
  "voided": false,
  "verbs": [
    "https://w3id.org/xapi/acrossx/verbs/searched"
  ],
  "personaIdentifier": "65ef0e8cfff35065a8efaec2",
  "processingQueues": [],
  "person": {
    "_id": "65ef0e8c99ffaefc9516664e",
    "display": "1710165537783x892345052938840600 - https://becomino.com/users (xAPI Account)"
  },
  "__v": 1,
  "timestamp": "2024-03-11T14:03:06.821Z",
  "relatedActivities": [
    "https://becomino.com/search/autocomplete%3Dvente",
    "https://becomino.com/account",
    "https://becomino.com/board/404",
    "https://becomino.com/category/404"
  ],
  "relatedAgents": [
    "https://becomino.com/users|1710165537783x892345052938840600",
    "mailto:contact@becomino.com"
  ],
  "organisation": "626a340cccbcc9000aff1421",
  "_id": "65ef0f26c56582001cca4928",
  "registrations": [],
  "pendingForwardingQueue": []
}
```

## Architecture

```mermaid
classDiagram
   PLRS <|-- PLRS_PDC
   PLRS_PDC <|-- PLRS
   CC_PDC <|-- Consent_Contracts
   Consent_Contracts <|-- CC_PDC
   DVA_PDC <|-- Data_veracity_assurance
   Data_veracity_assurance <|-- DVA_PDC 
   DAI_PDC <|-- Decentralized_AI_training
   Decentralized_AI_training <|-- DAI_PDC
   PLRS_PDC <|-- CC_PDC
   CC_PDC <|-- PLRS_PDC
   PLRS_PDC <|-- DVA_PDC
   DVA_PDC <|-- PLRS_PDC
   PLRS_PDC <|-- DAI_PDC
   DAI_PDC <|-- PLRS_PDC
   PLRS: update()
   PLRS: exoprt_lms()
   PLRS: import_lms()
   PLRS: visualize()
   PLRS: synchronize()
   PLRS: local_access()
   class PLRS_PDC{
     identity()
     catalog()
     contract()
     consent()
   }
   class CC_PDC{
     identity()
     catalog()
     contract()
     consent()
   }
   class DVA_PDC{
     identity()
     catalog()
     contract()
     consent()
   }
   class DAI_PDC{
     identity()
     catalog()
     contract()
     consent()
   }
   class Consent_Contracts{
     bool week[7]
     int begin[7]
     int end[7]
     string trigger_keywords[]
     add_trigger_keyword(string)
     change_track()
   }
   class Data_veracity_assurance{
     bool homogeneous
     homogeneous()
   }
   class Decentralized_AI_training{
     run_algo()
   }
```
PDC : Prometheus-X Dataspace Connector

The blocks depicted in the architecture graphic represent hypothetical functions, as their development has not yet been completed. However, we aim to communicate with the "consent contract" to transparently track users. This means that users will be able to personalize various parameters. Communication with the "data veracity assurance" will aim to harmonize data. As for "decentralize AI training", the aim is to send them anonymized (or non-anonymized) data to improve AI.


## Dynamic Behaviour

Behavior when exporting a dataset from the LMS :
```mermaid
sequenceDiagram
    participant User
    participant LRS
    participant PDC_LRS
    participant PDI
    participant Data_Intermediary
    participant PDC_PLRS
    participant PLRS

    User->>PDI: Agreement sent to transfer traces to PLRS by clicking on the LMS button
    PDI->>PDC_LRS: Data exchange trigger (including consent)
    PDC_LRS->>Data_Intermediary: Contract verification and policies
    Data_Intermediary->>PDC_LRS: Contract and policies verified
    PDC_LRS->>LRS: LRS gets data
    LRS->>PDC_LRS: send data to PDC LRS
    PDC_LRS->> PDC_PLRS:Send data to PDC PLRS
    PDC_PLRS->>PLRS: Send data to PLRS

```
PDC : Prometheus-X Dataspace Connector

Behavior when importing a dataset from the PLRS :

```mermaid
sequenceDiagram
   actor User as User
   User->>PLRS: Send dataset in different format than xAPI
   PLRS->>LRC: Send dataset in different format than xAPI
   LRC->>PLRS: Send dataset into xAPI format
   PLRS->>PLRS: Update visualization
```
PDC : Prometheus-X Dataspace Connector

Behavior when share a dataset from the PLRS :
```mermaid
sequenceDiagram
   actor User as user
   participant PLRS as PLRS
   participant PDI as PDI
   participant PDC_PLRS as PDC PLRS
   participant Data_intermediary as Data Intermediary
   participant PDC_external as PDC External
   participant External_LRS as External LRS

   User->>PLRS: Click on the button to share a dataset with external source
   PLRS->>PDI: Agreement sent to transfer traces to LRS (external source) by clicking on the PLRS button
   PDI->>PDC_PLRS: Data exchange trigger (including consent)
   PDC_PLRS->>Data_intermediary: Contract verification and policies
   Data_intermediary->>PDC_PLRS: Contract and policies verified
   PDC_PLRS->>PLRS: Requests the dataset from the PLRS
   PLRS->>PDC_PLRS: PLRS sends data to PDC PLRS
   PDC_PLRS->>PDC_external: Send selected dataset
   PDC_external->>External_LRS: Send dataset to external LRS
```
PDC : Prometheus-X Dataspace Connector

## Configuration and deployment settings

### Deployment & installation

- The user must have created its Cozy cloud and installed it on its device (see [here](https://cozy.io/en/download/))

- Once installed, the user must go to cozy app store and select the PLRS app


### Error Scenarios Defined

The idea of the risk table is to define the probable causes of failure in order to estimate the probability of encountering this failure, to evaluate its secondary effects and therefore to plan preventive or corrective actions.


We will assign 3 scores on a scale of 1 to 10 to potential failures:

- **Detection** (risk of non-detection)

- **Occurrence** (probable occurrence, frequency of occurrence)

- **Severity of Effect** (consequences for the customer)



Criticality is calculated as follows:

`criticality = detection x occurrence x severity`



If criticality is greater than 10, then preventive action must be taken. If not, no action is required.


| ID  | Function involved                                  | Description of risk                                               | Effect of failure                                              | Cause of failure                                               | Evaluation              | Preventive actions                                                                 |
|-----|----------------------------------------------------|--------------------------------------------------------------------|-----------------------------------------------------------------|-----------------------------------------------------------------|-------------------------|------------------------------------------------------------------------------------|
| 1   | export/import learning statements from LMS to PLRS | Data may be lost during migration                                 | The student doesn't have his tracks in his PLRS                | Incorrect connection between PLRS and LMS                      | Detection: 2 Occurrence: 2 Severity: 9 Criticality: 36        | Set up recurring connection tests, Setting up an LRC between LMS and PLRS              |
| 2   | export/import learning statements from LMS to PLRS | LMS statements are not in xAPI format                             | LMS and PLRS cannot communicate with each other                | LMS-specific data format                                       | Detection: 1 Occurrence: 4 Severity: 10 Criticality: 40        | Implementation of the PDC, which makes data exchange completely secure, Have a program that detects duplicates |
| 3   | export/import learning statements from LMS to PLRS | Data could be transmitted to other non-targeted LRSs              | Exported data may be accessible to unauthorized persons         | They are not properly secured                                  | Detection: 6 Occurrence: 1 Severity: 9 Criticality: 54         | Test the cloud service's scalability, Conduct pre-development workshops to ascertain user requirements and use accessibility tools                |
| 4   | export/import learning statements from LMS to PLRS | The same data can be exported several times                       | Wrong visualization and learning path                          | Duplicate data                                                 | Detection: 1 Occurrence: 6 Severity: 6 Criticality: 36         | Test the cloud service's scalability                                                |
| 5   | export/import learning statements from LMS to PLRS | The PLRS doesn't have enough storage space for all statements     | No more statement import/export                                | Too little storage                                             | Detection: 1 Occurrence: 3 Severity: 9 Criticality: 24         | Conduct pre-development workshops to ascertain user requirements                      |
| 6   | export/import learning statements from LMS to PLRS | The system may require downtime for large imports/exports          | Disrupting normal operations                                   | Low-performance servers                                        | Detection: 1 Occurrence: 3 Severity: 4 Criticality: 12         | Set up recurring connection tests, Synchronize regularly, not in real time             |
| 7   | export/import learning statements from LMS to PLRS | Graphs don't update                                               | Poor information on learning path                              | Slow update due to servers                                     | Detection: 1 Occurrence: 2 Severity: 2 Criticality: 4          | Test the cloud service's scalability                                                |
| 8   | export/import learning statements from LMS to PLRS | Poorly designed graphics                                          | No use of the platform                                         | Graphs are misleading                                          | Detection: 4 Occurrence: 3 Severity: 8 Criticality: 96         | Update documentation/history of all actions (import/export, synchronization), Have a maintenance team |
| 9   | export/import learning statements from LMS to PLRS | Wrong design choices: colors, shapes, ...                         | No use of the platform                                         | Visual choices such as colors and graphics can subliminally influence the perception of data. Graphs are non-inclusive | Detection: 4 Occurrence: 2 Severity: 8 Criticality: 96         | Update documentation/history of all actions (import/export, synchronization), Have a maintenance team |
| 10  | visualize learning statements in PLRS              | Errors in synchronization can lead to data loss or partial recordings | Distorted data                                               | Incorrect connection between PLRS and LMS                      | Detection: 2 Occurrence: 4 Severity: 9 Criticality: 36         | Set up recurring connection tests, Setting up an LRC between LMS and PLRS              |
| 11  | visualize learning statements in PLRS              | The possibility of data conflicts can compromise information integrity | Distorted data                                               | Changes are made simultaneously in both LRS                    | Detection: 7 Occurrence: 5 Severity: 7 Criticality: 196        | Conduct pre-development workshops to ascertain user requirements and use accessibility tools                |
| 12  | visualize learning statements in PLRS              | Synchronization processes can consume a lot of resources          | Disrupting normal operations                                   | Impacting the performance of real-time LRS systems             | Detection: 1 Occurrence: 3 Severity: 3 Criticality: 15         | Set up recurring connection tests, Synchronize regularly, not in real time             |
| 13  | synchronize PLRS data with external LRS (regular push) | The synchronization process can require downtime that affects system availability, especially when large quantities of data need to be synchronized. | Reconnecting the PLRS and the new LRS/LMS                     | Low-performance servers                                        | Detection: 1 Occurrence: 2 Severity: 4 Criticality: 12         | Test the cloud service's scalability                                                |
| 14  | synchronize PLRS data with external LRS (regular push) | The organization may decide to change its LRS/LMS                | No learner monitoring of synchronization. No data transfer transparency | Change of LRS/LMS                                              | Detection: 1 Occurrence: 4 Severity: 3 Criticality: 2          | Update documentation/history of all actions (import/export, synchronization), Have a maintenance team |
| 15  | synchronize PLRS data with external LRS (regular push) | Make sure that synchronization has been successful                | Distorted data                                               | No documentation                                               | Detection: 1 Occurrence: 3 Severity: 7 Criticality: 12         | Update documentation/history of all actions (import/export, synchronization), Have a maintenance team |
| 16  | synchronize PLRS data with external LRS (regular push) | Errors in the synchronization process can lead to complete synchronization failures, requiring manual diagnosis and correction | Distorted data                                               | Errors in the synchronization                                   | Detection: 7 Occurrence: 3 Severity: 7 Criticality: 147        | Set up recurring connection tests, Synchronize regularly, not in real time             |

## Third Party Components & Licenses

External components and licenses:

- Cozy cloud, [open source](https://github.com/cozy/cozy-stack), [license ](https://github.com/cozy/cozy-stack?tab=AGPL-3.0-1-ov-file#readme)[GPLv3](https://github.com/cozy/cozy-stack?tab=AGPL-3.0-1-ov-file#readme)

## OpenAPI Specification

*In the future: link your OpenAPI spec here.*

```yml
openapi: 3.0.0 \
info: \
     version: 0.0.1 \
     title: Personal Learning Record Store \
   description: Personal Learning Record Store (LRS) allows individuals to store and manage their own learning records in their cloud drive. PLRS allows individuals to keep track of their learning activities, achievements, and progress through their whole life. They can easily share these data with others if, or when, they choose to. \
paths: \
     /list: \
          get: \
               description: Returns a list of stuff \
                    responses: \
                         '200': \
                              description: Successful response
```

## Codebase : Mockup version
To get a functional understanding of this mockup and see some sample traces, go here : https://github.com/Prometheus-X-association/plrs/blob/main/docs/Images/PLRS%20-%20Mockup%20.pdf

To have a write access to the traces make a request on this mockup document : https://docs.google.com/document/d/14F-7Q9_LMLnUqvDx8EzAVrVWhLo93P5dHB3c3acYNRg/edit?usp=sharing
To have a read access to the traces make a request on this mockup document: https://docs.google.com/document/d/1lr1r_naA1FR77qQzOdxbiCH6SZsunFcqvHBJ2JPOlZI/edit?usp=sharing 

### PUT
description: Store a single statement as a single member of a set.

### POST
description: "Store a set of statements (or a single statement as a single member of a set).

### GET
description: Read a single xAPI Statement or multiple xAPI Statements.



## Test Specification



The Personal Learning Record Store tests ensure that:

- Functionality is efficient

- Potential risks are under control

- Users are satisfied



### Test Plan



The PLRS testing strategy will focus on ensuring the accuracy, reliability, and performance of its functionality. We will use a combination of unit testing, integration testing, and user interface testing. The test environment will reproduce conditions similar to those in production in order to accurately validate BB behavior. Acceptance criteria will be defined on the basis of user stories, functional requirements, and performance criteria.



### Methodology



We will run manual and automatic tests.



#### Manual Scenario



Using the personas, user stories, user flow, and data flow from the DAPO-X use case, we established several test scenarios.
For your information, the tests will be extended in the future.

**User triggers in Constellation the transfer of their data from Constellation to PLRS. It is a one time transfer.**

- The learner completes the "Test d'entrée en formation" activity on Constellation
    - https://constellation.inokufu.com/mod/quiz/view.php?id=374
    - It scores 6/10

- He obtains the certificate of completion
    - https://constellation.inokufu.com/course/view.php?id=25

- He finishes the "Introduction aux Data Spaces" course

- He exports his data to his PLRS (in LMS frontend)

Validation : This scenario is validated if the PLRS display statements of learning. In particular these 3 statements :
- The student completed the "Test d'entrée en formation" with 6/10.
- The student graded the certificate.
- The student completed the "Introduction aux data spaces" course.

**User triggers in PLRS the transfer of their data from Constellation to PLRS. It is a one time transfer**
- The learner completes the "Quizz de renforcement Prompt" activity on Constellation
    - https://constellation.inokufu.com/mod/hvp/view.php?id=29
    - It scores 7/10
    
- He transfers his data from LMS to his PLRS (in PLRS frontend)

Validation : This scenario is validated if the PLRS shows statements of learning. In particular this statement :
- The student completed the "Quizz de renforcement Prompt" with 7/10.

**User triggers in PLRS the transfer of their data from Constellation to PLRS. It is a regular transfer (every week)**
- The learner completes the activity "Lombricomposter"
    - Date: 01.10.2024
    - https://constellation.inokufu.com/mod/hvp/view.php?id=119

- The learner completes the course "Apprendre à composter en maison ou appartement"
    - Date: 02.10.2024
    - https://constellation.inokufu.com/course/view.php?id=9

- The learner completes the course “Sécurité incendie” 
- Obtain the certificate
    - Date: 06.10.2024
    - https://constellation.inokufu.com/course/view.php?id=12

Validation : This scenario is validated if the PLRS shows statements of learning. In particular these 5 statements in these dates (if the transfer is all saturday):
05.10.2024
- The student completed the "Lombricomposter" activity.
- The student graded the certificate.
- The student completed the "Apprendre à composter en maison ou appartement" course.
12.10.2024
- The student graded the certificate.
- The student completed the "Sécurité incendie" course.

**User triggers in PLRS the transfer of their data from PLRS to external app. It is a one time transfer.**
- The learner completes the course “Constellation, un atout pédagogique?”
    - Date: 04.07.2024
    - https://constellation.inokufu.com/course/view.php?id=8

- The learner completes the course “Sécurité incendie”
- He obtain the certificate
    - Date: 11.07.2024
    - https://constellation.inokufu.com/course/view.php?id=12
 
- He exports his data to the school's LRS (https://XXX.com/data/xAPIx), in PLRS frontend.

Validation : This scenario is validated if the school's LRS display statements of learning.

**User triggers in PLRS the transfer of their data from PLRS to external app. It is a regular transfer (every week).**
The user has given access to his data to the school's LRS (https://XXX.com/data/xAPIx)

- The learner completes the course “Constellation, un atout pédagogique?”
    - Date: 04.07.2024
    - https://constellation.inokufu.com/course/view.php?id=8

- The learner completes the course “Sécurité incendie”
- He obtain the certificate
    - Date: 11.07.2024
    - https://constellation.inokufu.com/course/view.php?id=12

Validation : This scenario is validated if the school's LRS display statements of learning.


### Automatic Test



**Auto1: Transfer test**

- Automatic transfer of learning statements once a week.



**Auto2: Scalability test**

- Automatic transfer of learning statements 1 time per week, 1 time per day, 2 times per day.


### UI test (where relevant)

Please note that the following visuals are intended as projections only. UX/UI work will be carried out later in the process.

![Cozy store](https://github.com/Prometheus-X-association/plrs/assets/129832540/54e17b27-27e3-4791-be1f-f3ea78e188e2)

![Cosy store - PLRS](https://github.com/Prometheus-X-association/plrs/assets/129832540/89f5b741-6d72-4368-b04c-cbd621b1bdd3)

![PLRS](https://github.com/Prometheus-X-association/plrs/assets/129832540/23e04cd1-59d8-40d4-a3ce-2bdcd615be96)


## Partners & roles
[Inokufu](https://www.inokufu.com/) (BB leader): 
- Organize workshops
- Monitor partner progress
- Develop backend of PLRS

[Cozy cloud](https://cozy.io/en/): 
- Host infrastructure
- Develop frontend/application of PLRS
- Deploy PTX dataspace connector for PLRS

## Usage in the dataspace
The PLRS will be used in the service chain :
- Personal learning record: Sharing LMS/Moodle Data for Visualization
  
![Diagram of service chain Sharing LMS/Moodle Data for Visualization](Images/BB%20Service%20chains%20_%20LRS%20Learning%20Records%20store.pptx%20(3).png)
PDC : Prometheus-X Dataspace Connector

- Decentralized AI training: Training of trustworthy AI models
  ![BB Service chains - Decentralized training](https://github.com/user-attachments/assets/e54b5409-8d7a-45e3-bc56-54b7d8738417)
