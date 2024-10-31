# Mock-up PLRS 

## How have we carried out the mock-up for our building block 'PLRS'?

The following document is designed to show the process through which Inokufu created the mock-up for the Building Block 'Personal Learning Record Store (PLRS).'

The data push related to this mock-up aims to simulate the transfer of data from an external application, such as an organizational LRS, to the PLRS and vice versa, represented in this case by our LRS, Learning Locker.

To elaborate, PLRS is a building block aimed at being a learning records store managed by the user themselves, where they can store, visualize, and share the learning records they have generated throughout their learning journey across various training organizations or educational institutions. This is allowed in part due to the fact that the records are stored in an interoperable format: xAPI.


![PLRS mockup a](https://github.com/user-attachments/assets/b386071f-9c64-4521-989a-a124a86f20c2)

In this example image, we can see how the user would be able to visualize their learning journey through various parameters, such as obtained certifications, consulted learning objects, ongoing trainings, among many other variables that could be considered interesting parameters for evaluating an individual's learning path. These visualizations are given by way of example. Changes may occur.

## How to Configure the Learning Records Store?

To execute the mock-up, a store was created in the Learning Records Store "Learning Locker," named "Mockup PLRS," with two clients: one to receive data from the BB in question - **Mockup PLRS Read** - and another to send data - **Mockup PLRS Write**.

In terms of configuring both clients, as seen in the following screenshot, we set up one of them to be able to receive xAPI statements, so we configured it to **'Read all'** and linked it with the store **“Mockup PLRS.”**

Once that client was created, we proceeded to create the other one through which we will send xAPI statements to an external endpoint. This could be the case if the user chooses to share their records with a university. In this way, they would send their learning traces to the university's LRS. So, to configure this client, we clicked on **“Write statements (must be used with a read scope)"** and linked it too with the store **“Mockup PLRS.”**

It should be noted that the **'key'** and the **'secret'** are necessary credentials to connect the clients of a store with the endpoint it will communicate with, which in this case would be the extension account of the organization that is the protagonist of this data push from PLRS to its LRS. 

We can access these credentials by going to the settings section, then to clients, and finally selecting the client for which we want to find out the key and the secret. Furthermore, if they require our read or write keys, they should contact us. You can find our emails at the bottom of the document.

## Nature of the Data That Have Been Sent

The data push has already been triggered, and we received 390 xAPI statements. These records pertain to different actions made by several users that could be understood as learning activities or actions through which they build a certain knowledge. Based on this, the statements we have received contain xAPI verbs such as **"accessed,"** **"liked,"** **"opened,"** or **"searched."**
![Uploading PLRS - Mockup b.png…]()

### Example of a Particular xAPI Statement Received by the Mockup PLRS Store

We will use the following xAPI statement received in the store corresponding to the PLRS mockup as an example to demonstrate how this mockup addresses educational needs.
![mockup plrs c](https://github.com/user-attachments/assets/8ad3f616-e0a1-48e6-bb27-42740cd9f245)

The following two statements correspond to the record of two different users who would own a PLRS:

- The first statement reflects the access made by a user to the section **“Become Pro in Data Analysis”** of Becomino’s platform.
- The second statement pertains to a like given by another user to an activity displayed in the section of the first statement, which is titled **"Data Analysis and Visualization with Python"**. Its provider is Udemy, and the URL is: [https://www.udemy.com/course/analyse-et-visualisation-de-data-avec-python](https://www.udemy.com/course/analyse-et-visualisation-de-data-avec-python).

From a pedagogical perspective, the ability to retrieve xAPI statements that reflect interactions with courses, learning objects, or the possibility of sharing them with other entities opens up a vast range of possibilities. As these two statements clearly show, we as educators or trainers can gain a deeper understanding of how our learners engage with our courses. At the same time, learners or users can receive better feedback from their educators by sharing their records. They could also demonstrate self-acquired competencies to recruiters or even share statements to receive personalized training.

While analyzing only 2 statements would yield limited insights, we have gathered 390 statements. This substantial dataset allows an organization to comprehensively understand the user’s interests and learning methods. Consequently, this enables the organization to offer customized training. In this particular case, an organization, based on an analysis of its learning records, would be able to offer a Python course tailored to the professional field in which the user operates.

### The statements itself:



`1725541038216x297089120079349500 accessed Devenir Pro en Analyse de données`



#### Example of xAPI Statement



```json

{

  "stored": "2024-09-06T09:34:23.975Z",

  "priority": "MEDIUM",

  "active": true,

  "client": "66b381ac128b7e5fbbaef81c",

  "lrs_id": "66b37b2f128b7e293caef818",

  "activities": [

    "https://becomino.com/board/devenir-pro-analyse-donnees-1648372285523x867799490361819100"

  ],

  "agents": [

    "https://becomino.com/users|1725541038216x297089120079349500"

  ],

  "statement": {

    "authority": {

      "objectType": "Agent",

      "name": "Mockup PLRS write",

      "mbox": "mailto:contact@inokufu.com"

    },

    "stored": "2024-09-06T09:34:23.975Z",

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

        "name": "1725541038216x297089120079349500"

      },

      "objectType": "Agent"

    },

    "timestamp": "2024-09-05T13:31:29.777Z",

    "verb": {

      "id": "https://w3id.org/xapi/netc/verbs/accessed",

      "display": {

        "en-US": "accessed"

      }

    },

    "object": {

      "id": "https://becomino.com/board/devenir-pro-analyse-donnees-1648372285523x867799490361819100",

      "definition": {

        "name": {

          "fr": "Devenir Pro en Analyse de données"

        },

        "type": "http://adlnet.gov/expapi/activities/link"

      },

      "objectType": "Activity"

    }

  },

  "timestamp": "2024-09-05T13:31:29.777Z",

  "relatedActivities": [

    "https://becomino.com/board/devenir-pro-analyse-donnees-1648372285523x867799490361819100",

    "https://becomino.com/home",

    "https://becomino.com/board/404",

    "https://becomino.com/category/404"

  ]

}

```



#### Example of xAPI Statement



`1725541038216x297089120079349500 liked Data Science: Analyse de données avec Python`



```json

{

  "stored": "2024-09-06T09:34:23.975Z",

  "priority": "MEDIUM",

  "active": true,

  "completedForwardingQueue": [],

  "failedForwardingLog": [],

  "client": "66b381ac128b7e5fbbaef81c",

  "lrs_id": "66b37b2f128b7e293caef818",

  "completedQueues": [

    "STATEMENT_FORWARDING_QUEUE",

    "STATEMENT_PERSON_QUEUE",

    "STATEMENT_QUERYBUILDERCACHE_QUEUE"

  ],

  "activities": [

    "https://www.udemy.com/course/analyse-et-visualisation-de-data-avec-python"

  ],

  "hash": "aabac6d68f7816d95a5e9436c8898cd05df32b57",

  "agents": [

    "https://becomino.com/users|1725541038216x297089120079349500"

  ],

  "statement": {

    "authority": {

      "objectType": "Agent",

      "name": "Mockup PLRS write",

      "mbox": "mailto:contact@inokufu.com"

    },

    "stored": "2024-09-06T09:34:23.975Z",

    "context": {

      "contextActivities": {

        "parent": [

          {

            "id": "https://becomino.com/board/devenir-pro-analyse-donnees-1648372285523x867799490361819100",

            "objectType": "Activity"

          }

        ],

        "category": [

          {

            "id": "https://becomino.com/category/numerique",

            "objectType": "Activity"

          }

        ],

        "grouping": [

          {

            "id": "https://becomino.com/board/devenir-pro-analyse-donnees",

            "objectType": "Activity"

          }

        ]

      },

      "language": "fr",

      "extensions": {

        "http://schema.inokufu.com/becomino/board": {

          "id": "https://becomino.com/board/devenir-pro-analyse-donnees",

          "name": {

            "fr": "Devenir Pro en Analyse de données"

          }

        }

      }

    },

    "actor": {

      "account": {

        "homePage": "https://becomino.com/users",

        "name": "1725541038216x297089120079349500"

      },

      "objectType": "Agent"

    },

    "timestamp": "2024-09-05T13:29:51.066Z",

    "version": "1.0.0",

    "id": "e54fd84e-97fa-4877-b6e0-4ed851110ac9",

    "verb": {

      "id": "https://w3id.org/xapi/acrossx/verbs/liked",

      "display": {

        "en-US": "liked"

      }

    },

    "object": {

      "id": "https://www.udemy.com/course/analyse-et-visualisation-de-data-avec-python",

      "definition": {

        "name": {

          "fr": "Data Science : Analyse de donnees avec Python"

        },

        "description": {

          "fr": "Si vous souhaitez entrer dans le monde de la Data science et apprendre a Analyser et Visualiser des donnees, ce cours est fait pour vous ! Ce cours traite des bibliotheques scientifiques de Python particulierement utilisees en Data Science: Numpy, Pandas et Matplotlib.Tout au long de la formation, o..."

        },

        "type": "http://adlnet.gov/expapi/activities/link",

        "extensions": {

          "http://schema.inokufu.com/learning-object/type": "MOOC",

          "http://schema.inokufu.com/learning-object/bloom": "understand",

          "http://schema.inokufu.com/learning-object/provider": "Udemy",

          "http://schema.inokufu.com/learning-object/picture": "https://img-c.udemycdn.com/course/750x422/1620090_0efb_4.jpg"

        }

      },

      "objectType": "Activity"

    }

  },

  "hasGeneratedId": true,

  "deadForwardingQueue": [],

  "voided": false,

  "verbs": [

    "https://w3id.org/xapi/acrossx/verbs/liked"

  ],

  "personaIdentifier": "66d9aad6536c52d8ba7b4248",

  "processingQueues": [],

  "person": {

    "_id": "66d9aad6e98283f3caea3109",

    "display": "1725541038216x297089120079349500 - https://becomino.com/users (xAPI Account)"

  },

  "__v": 1,

  "timestamp": "2024-09-05T13:29:51.066Z",

  "relatedActivities": [

    "https://www.udemy.com/course/analyse-et-visualisation-de-data-avec-python",

    "https://becomino.com/board/devenir-pro-analyse-donnees-1648372285523x867799490361819100",

    "https://becomino.com/board/devenir-pro-analyse-donnees",

    "https://becomino.com/category/numerique"

  ],

  "relatedAgents": [

    "https://becomino.com/users|1725541038216x297089120079349500",

    "mailto:contact@inokufu.com"

  ],

  "organisation": "626a340cccbcc9000aff1421",

  "_id": "66dacca07048fd001d44cec2",

  "registrations": [],

  "pendingForwardingQueue": []

}

```



## Use Cases



We can consider possible scenarios in which xAPI statements like these could be shared:



- A company/edtech providing courses that wants to send data to the future PLRS. This could test data portability.

- A company/edtech that wants to analyze data and create graphs or personalize learning with data.



## Contact



If you are interested in obtaining a read or write key, contact us directly. Send us your use case, the type of your data, the number of traces you want to send or receive, and what kind of trace you need.



- **Sebastian**: [sebastian.utard@inokufu.com](mailto:sebastian.utard@inokufu.com)

- **Lauriane**: [lauriane.marxer@inokufu.com](mailto:lauriane.marxer@inokufu.com)

```
