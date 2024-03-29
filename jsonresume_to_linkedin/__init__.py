import os
import json
from linkedin_api import Linkedin


USERNAME = os.environ.get("LINKEDIN_USERNAME")
PASSWORD = os.environ.get("LINKEDIN_PASSWORD")

api = Linkedin(USERNAME, PASSWORD)

user_profile = api.get_user_profile()
if not user_profile:
    exit(1)

user_urn = user_profile["miniProfile"]["dashEntityUrn"]
user_urn_id = user_urn.split(":")[-1]

# add a link/featured item
# api._post(
#     "/graphql?action=execute&queryId=voyagerIdentityDashProfileTreasuryMedia.937a6ea5945f9fb6bbeb31e78d3ea85f",
#     json={
#         "variables": {
#             "entities": [
#                 {
#                     "data": {"Url": "https://mbund.dev/about/"},
#                     "multiLocaleDescription": [{"key": "en_US", "value": "desc2"}],
#                     "multiLocaleTitle": [
#                         {"key": "en_US", "value": "About Me | Mark's Blog2"}
#                     ],
#                 }
#             ],
#             "sectionUrn": "urn:li:fsd_profile:ACoAAEHkM3oBc-Pt-2pasLeYvJD3eoRDRw7BqgU",
#         },
#         "queryId": "voyagerIdentityDashProfileTreasuryMedia.937a6ea5945f9fb6bbeb31e78d3ea85f",
#     },
# )


def submit_changes(changes):
    body = {
        "variables": {"formElementInputs": changes},
        "queryId": "voyagerIdentityDashProfileEditFormPages.6d94a566c1bd618c24bd06295de90c2e",
        "includeWebMetadata": True,
    }
    # print(json.dumps(body))

    return api._post(
        "/graphql?action=execute&queryId=voyagerIdentityDashProfileEditFormPages.6d94a566c1bd618c24bd06295de90c2e",
        json=body,
    ).json()


def make_change(urn, values):
    return {"formElementUrn": urn, "formElementInputValues": values}


def update_from_jsonresume(profile, resume):
    # Summary
    about = resume["basics"]["summary"]
    if profile["summary"] != about:
        submit_changes(
            [
                make_change(
                    f"urn:li:fsd_profileEditFormElement:(SUMMARY,{user_urn},/summary)",
                    [{"textInputValue": about}],
                )
            ]
        )
        print(f"Updated {about}")

    # Experiences
    experiences = [
        (
            work,
            next(
                (
                    experience
                    for experience in profile["experience"]
                    if experience["companyName"] == work["name"]
                    and experience["title"] == work["position"]
                ),
                None,
            ),
        )
        for work in resume["work"]
    ]
    for work, li_experience in experiences:
        if li_experience:
            company_urn = li_experience["entityUrn"].split("(")[-1][:-1]
        else:
            company_urn = f"{user_urn_id},-1"

        changes = []

        description = ""
        if "summary" in work:
            description = work["summary"] + "\n\n"
        description += "\n".join([f"- {highlight}" for highlight in work["highlights"]])
        if not li_experience or description != li_experience["description"]:
            changes.append(
                make_change(
                    f"urn:li:fsd_profileEditFormElement:(POSITION,urn:li:fsd_profilePosition:({company_urn}),/description)",
                    [{"textInputValue": description}],
                )
            )

        dateRange = {
            "startDate": {
                "month": int(work["startDate"].split("-")[1]),
                "year": int(work["startDate"].split("-")[0]),
            },
        }
        if "endDate" in work:
            dateRange["endDate"] = {
                "month": int(work["endDate"].split("-")[1]),
                "year": int(work["endDate"].split("-")[0]),
            }
        if not li_experience or dateRange != li_experience["timePeriod"]:
            dateRangeInputValue = {
                "start": dateRange["startDate"],
            }
            if "endDate" in dateRange:
                dateRangeInputValue["end"] = dateRange["endDate"]
            changes.append(
                make_change(
                    f"urn:li:fsd_profileEditFormElement:(POSITION,urn:li:fsd_profilePosition:({company_urn}),/dateRange)",
                    [{"dateRangeInputValue": dateRangeInputValue}],
                )
            )

        if not li_experience:  # or li_experience["title"] != work["position"]
            changes.append(
                make_change(
                    f"urn:li:fsd_profileEditFormElement:(POSITION,urn:li:fsd_profilePosition:({company_urn}),/title)",
                    [{"textInputValue": work["position"]}],
                )
            )

        if not li_experience:  # or li_experience["companyName"] != work["name"]
            company = api.search_companies(work["name"])[0]
            changes.append(
                make_change(
                    f"urn:li:fsd_profileEditFormElement:(POSITION,urn:li:fsd_profilePosition:({company_urn}),/requiredCompany)",
                    [
                        {
                            "entityInputValue": {
                                "inputEntityName": work["name"],
                                "inputEntityUrn": f"urn:li:fsd_company:{company['urn_id']}",
                            }
                        }
                    ],
                )
            )

        if (
            not li_experience
            or "locationName" not in li_experience
            or li_experience["locationName"] != work["location"]
        ) and "location" in work:
            changes.append(
                make_change(
                    f"urn:li:fsd_profileEditFormElement:(POSITION,urn:li:fsd_profilePosition:({company_urn}),/geoPositionLocation)",
                    [{"entityInputValue": {"inputEntityName": work["location"]}}],
                )
            )

        if changes:
            submit_changes(changes)
            if li_experience:
                print(f"Updated experience {work['name']} {work['position']}")
            else:
                print(f"Created experience {work['name']} {work['position']}")

    to_be_deleted_li_experiences = [
        experience
        for experience in profile["experience"]
        if not any(
            [
                work["name"] == experience["companyName"]
                and work["position"] == experience["title"]
                for work in resume["work"]
            ]
        )
    ]
    for li_experience in to_be_deleted_li_experiences:
        company_urn_id = li_experience["entityUrn"].split(",")[-1][:-1]
        api._fetch(
            f"/graphql?includeWebMetadata=true&variables=(profileEntityUrn:urn%3Ali%3Afsd_profilePosition%3A%28{user_urn_id}%2C{company_urn_id}%29)&queryId=voyagerIdentityDashProfileEditFormPages.ff79b6313d5cf206e86733e7a6622f42",
            headers={
                "accept": "application/vnd.linkedin.normalized+json+2.1",
                "x-li-pem-metadata": "Voyager - Profile=position-profile-edit-form-delete",
            },
        )

        print(
            f"Deleted experience {li_experience['companyName']} {li_experience['title']}"
        )

    # Skills
    skills = sum([skill["keywords"] for skill in resume["skills"]], [])
    linkedin_skills = [
        skill["name"] for skill in api.get_profile_skills(urn_id=user_urn_id)
    ]
    linkedin_skills = [skill.split(" (")[0] for skill in linkedin_skills]
    skills = [skill for skill in skills if skill not in linkedin_skills]
    for skill in skills:
        submit_changes(
            [
                make_change(
                    f"urn:li:fsd_profileEditFormElement:(SKILL_AND_ASSOCIATION,urn:li:fsd_skill:({user_urn_id},-1),/name)",
                    [{"entityInputValue": {"inputEntityName": skill}}],
                )
            ]
        )
        print(f"Added skill {skill}")

    # Projects
    projects = [
        (
            project,
            next(
                (
                    linkedin_project
                    for linkedin_project in profile["projects"]
                    if linkedin_project["title"] == project["name"]
                ),
                None,
            ),
        )
        for project in resume["projects"]
    ]
    for project, linkedin_project in projects:
        if linkedin_project:
            project_urn = f"{user_urn_id},{linkedin_project['members'][0]['entityUrn'].split(',')[1]}"
        else:
            project_urn = f"{user_urn_id},-1"

        changes = []

        if not linkedin_project:  # or linkedin_project["title"] != project["name"]
            changes.append(
                make_change(
                    f"urn:li:fsd_profileEditFormElement:(PROJECT,urn:li:fsd_profileProject:({project_urn}),/title)",
                    [{"textInputValue": project["name"]}],
                )
            )

        description = "\n".join(
            [f"- {highlight}" for highlight in project["highlights"]]
        )
        if not linkedin_project or linkedin_project["description"] != description:
            changes.append(
                make_change(
                    f"urn:li:fsd_profileEditFormElement:(PROJECT,urn:li:fsd_profileProject:({project_urn}),/description)",
                    [{"textInputValue": description}],
                )
            )

        dateRange = {
            "startDate": {
                "month": int(project["startDate"].split("-")[1]),
                "year": int(project["startDate"].split("-")[0]),
            },
        }
        if "endDate" in project:
            dateRange["endDate"] = {
                "month": int(project["endDate"].split("-")[1]),
                "year": int(project["endDate"].split("-")[0]),
            }
        if (
            not linkedin_project
            or "timePeriod" not in linkedin_project
            or dateRange != linkedin_project["timePeriod"]
        ):
            dateRangeInputValue = {
                "start": dateRange["startDate"],
            }
            if "endDate" in dateRange:
                dateRangeInputValue["end"] = dateRange["endDate"]
            changes.append(
                make_change(
                    f"urn:li:fsd_profileEditFormElement:(PROJECT,urn:li:fsd_profileProject:({project_urn}),/dateRange)",
                    [{"dateRangeInputValue": dateRangeInputValue}],
                )
            )

        if changes:
            submit_changes(changes)
            if linkedin_project:
                print(f"Updated project {project['name']}")
            else:
                print(f"Created project {project['name']}")


def main():
    profile = api.get_profile(urn_id=user_urn_id)
    print("Got self profile")

    with open("resume.json", "r") as f:
        resume = json.load(f)
        update_from_jsonresume(profile, resume)


if __name__ == "__main__":
    main()
