import base64
import requests
import pandas as pd


SEARCH_URL = (
    "https://rest.arbeitsagentur.de/"
    "jobboerse/jobsuche-service/pc/v6/jobs"
)

DETAIL_URL = (
    "https://rest.arbeitsagentur.de/"
    "jobboerse/jobsuche-service/pc/v4/jobdetails/"
)

HEADERS = {
    "X-API-Key": "jobboerse-jobsuche"
}


def fetch_jobs(search_term="Werkstudent", location="Deutschland", size=10):
    """Search jobs from the Bundesagentur für Arbeit API."""

    params = {
        "was": search_term,
        "wo": location,
        "size": size
    }

    response = requests.get(
        SEARCH_URL,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json().get("ergebnisliste", [])


def fetch_job_details(reference_number):
    """Fetch full details for one job."""

    encoded_reference = base64.b64encode(
        reference_number.encode()
    ).decode()

    url = DETAIL_URL + encoded_reference

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def jobs_to_dataframe(jobs):
    """Convert jobs and their details into a DataFrame."""

    records = []

    for index, job in enumerate(jobs, start=1):

        reference_number = job.get("referenznummer", "")

        print(
            f"Fetching details {index}/{len(jobs)}: "
            f"{reference_number}"
        )

        try:
            details = fetch_job_details(reference_number)
        except requests.RequestException as error:
            print(f"Could not fetch details: {error}")
            details = {}

        locations = details.get(
            "stellenlokationen",
            job.get("stellenlokationen", [])
        )

        city = ""
        state = ""
        postal_code = ""

        if locations:
            address = locations[0].get("adresse", {})

            city = address.get("ort", "")
            state = address.get("region", "")
            postal_code = address.get("plz", "")

        records.append({
            "job_id": reference_number,
            "title": details.get(
                "stellenangebotsTitel",
                job.get("stellenangebotsTitel", "")
            ),
            "company": details.get(
                "firma",
                job.get("firma", "")
            ),
            "location": city,
            "state": state,
            "postal_code": postal_code,
            "job_type": details.get(
                "stellenangebotsart",
                job.get("stellenangebotsart", "")
            ),
            "description": details.get(
                "stellenangebotsBeschreibung",
                ""
            ),
            "salary": details.get(
                "verguetungsangabe",
                ""
            ),
            "contract": details.get(
                "vertragsdauer",
                ""
            ),
            "home_office": details.get(
                "homeofficemoeglich",
                False
            ),
            "posted_date": details.get(
                "datumErsteVeroeffentlichung",
                ""
            ),
            "source": "Bundesagentur für Arbeit"
        })

    return pd.DataFrame(records)


if __name__ == "__main__":

    print("Germany Student Job Intelligence")
    print("--------------------------------")
    print("Searching for Werkstudent jobs...")

    jobs = fetch_jobs(
        search_term="Werkstudent",
        location="Deutschland",
        size=10
    )

    print(f"Jobs found: {len(jobs)}")
    print()

    df = jobs_to_dataframe(jobs)

    output_file = "data/raw/jobs_api.csv"

    df.to_csv(output_file, index=False)

    print()
    print("Collection Complete")
    print("-------------------")
    print(f"Jobs collected: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Saved to: {output_file}")