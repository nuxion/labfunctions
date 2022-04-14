import os
from typing import Any, Dict, List, Optional

import google.auth
import google.auth.exceptions
from google.cloud import compute_v1


def google_implicit_auth(creds_file: Optional[str] = None):
    """
    Google implicit auth from here:
    https://cloud.google.com/docs/authentication/production#obtaining_and_providing_service_account_credentials_manually

    and here:
    https://github.com/googleapis/python-compute/blob/main/samples/snippets/instances/create.py
    """
    try:
        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            creds, default_project_id = google.auth.default()
        else:
            creds, default_project_id = google.auth.load_credentials_from_file(
                creds_file
            )

        return creds, default_project_id
    except google.auth.exceptions.DefaultCredentialsError:
        print(
            "Please use `gcloud auth application-default login` "
            "or set GOOGLE_APPLICATION_CREDENTIALS to use this script."
        )
