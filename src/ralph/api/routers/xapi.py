"""API routes related to other routes of the xAPI standard."""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/xAPI",
)

# TODO: Add all the missing routes when they will be built
@router.get("/about")
async def about():
    return JSONResponse(
        {
            "version":[
                "1.0.0",
                "1.0.1",
                "1.0.2",
                "1.0.3",
                "2.0.0"
            ],
            "extensions":{
                "xapi":{
                    "statements":{
                        "name":"Statements",
                        "methods":[
                            "GET",
                            "POST",
                            "PUT",
                            "HEAD"
                        ],
                        "endpoint":"/xAPI/statements",
                        "description":"Endpoint to submit and retrieve XAPI statements."
                    }
                }
            }
        }
    )
