"""Human-authored, section-scoped candidate questions for the local corpus."""

from typing import NamedTuple


class QuerySpec(NamedTuple):
    key: str
    query: str
    category: str
    intent: str
    sections: tuple[str, ...]
    rationale: str


ALL_SECTIONS = ("professional_summary", "skills", "experience", "projects", "education", "certifications", "awards", "publications", "additional_sections")


QUERY_SPECS = [
    QuerySpec("skills-01", "List every technical skill recorded for this candidate.", "technical_skills", "SKILL_SEARCH", ("skills",), "Requests the full skills inventory."),
    QuerySpec("skills-02", "What technologies and tools are included in the profile?", "technical_skills", "SKILL_SEARCH", ("skills",), "Requests all listed technologies and tools."),
    QuerySpec("skills-03", "Summarize the candidate's complete skills list.", "technical_skills", "SKILL_SEARCH", ("skills",), "Requests every skill entry."),
    QuerySpec("skills-04", "Which technical abilities does the candidate document?", "technical_skills", "SKILL_SEARCH", ("skills",), "Requests all documented technical abilities."),
    QuerySpec("skills-05", "Give me the full programming and technical skills inventory.", "technical_skills", "SKILL_SEARCH", ("skills",), "Requests the complete technical inventory."),
    QuerySpec("skills-06", "What areas of technical proficiency are listed?", "technical_skills", "SKILL_SEARCH", ("skills",), "Requests all proficiency and skill entries."),
    QuerySpec("projects-01", "List every project in the candidate's profile.", "projects", "PROJECT_SEARCH", ("projects",), "Requests all project memories."),
    QuerySpec("projects-02", "What portfolio projects are documented?", "projects", "PROJECT_SEARCH", ("projects",), "Portfolio is used as a project synonym."),
    QuerySpec("projects-03", "Summarize all of the candidate's project work.", "projects", "PROJECT_SEARCH", ("projects",), "Requests every project entry."),
    QuerySpec("projects-04", "Which projects and prototypes appear in the profile?", "projects", "PROJECT_SEARCH", ("projects",), "Requests the complete set of project memories."),
    QuerySpec("projects-05", "Tell me about all independent or portfolio work listed.", "projects", "PROJECT_SEARCH", ("projects",), "Requests all listed project work."),
    QuerySpec("projects-06", "What has the candidate built, according to the project section?", "projects", "PROJECT_SEARCH", ("projects",), "Explicitly asks for all project-section evidence."),
    QuerySpec("experience-01", "List all work experience entries.", "work_experience", "EXPERIENCE_SEARCH", ("experience",), "Requests every work-history memory."),
    QuerySpec("experience-02", "Summarize the candidate's complete employment history.", "work_experience", "EXPERIENCE_SEARCH", ("experience",), "Requests all employment entries."),
    QuerySpec("experience-03", "What professional experience is recorded in the profile?", "work_experience", "EXPERIENCE_SEARCH", ("experience",), "Requests all professional experience memories."),
    QuerySpec("experience-04", "Outline every role, employer, and responsibility listed.", "work_experience", "EXPERIENCE_SEARCH", ("experience",), "Requests the complete work-history record."),
    QuerySpec("experience-05", "Which jobs and career roles are documented?", "work_experience", "EXPERIENCE_SEARCH", ("experience",), "Requests all job and role entries."),
    QuerySpec("experience-06", "Give me the full work-history timeline from the resume.", "work_experience", "EXPERIENCE_SEARCH", ("experience",), "Requests all experience records and dates."),
    QuerySpec("education-01", "List every education entry in the profile.", "education", "EDUCATION_SEARCH", ("education",), "Requests all education memories."),
    QuerySpec("education-02", "Summarize the candidate's complete academic background.", "education", "EDUCATION_SEARCH", ("education",), "Requests all academic records."),
    QuerySpec("education-03", "What degrees, institutions, and study history are documented?", "education", "EDUCATION_SEARCH", ("education",), "Requests all education details."),
    QuerySpec("education-04", "Where and when did the candidate study, according to the profile?", "education", "EDUCATION_SEARCH", ("education",), "Requests all education entries and dates."),
    QuerySpec("certs-01", "List all certifications recorded for the candidate.", "certifications", "CERTIFICATION_SEARCH", ("certifications",), "Requests every certification memory."),
    QuerySpec("certs-02", "Which certificates and credentials are documented?", "certifications", "CERTIFICATION_SEARCH", ("certifications",), "Requests all certificate records."),
    QuerySpec("certs-03", "Summarize the candidate's complete certification list.", "certifications", "CERTIFICATION_SEARCH", ("certifications",), "Requests every certification entry."),
    QuerySpec("certs-04", "What formal certificates does this profile mention?", "certifications", "CERTIFICATION_SEARCH", ("certifications",), "Requests all formal certificate memories."),
    QuerySpec("general-01", "Give me a complete overview of the candidate's profile.", "general_profile", "GENERAL_SEARCH", ALL_SECTIONS, "Requests an overview across every available profile section."),
    QuerySpec("general-02", "What information is recorded across the full candidate profile?", "general_profile", "GENERAL_SEARCH", ALL_SECTIONS, "Requests all profile sections rather than one category."),
    QuerySpec("general-03", "Describe the candidate's overall professional background and qualifications.", "general_profile", "GENERAL_SEARCH", ALL_SECTIONS, "Broad question that should not apply a single-section filter."),
    QuerySpec("general-04", "Summarize the full set of details available about this candidate.", "general_profile", "GENERAL_SEARCH", ALL_SECTIONS, "Requests a full-profile summary."),
    QuerySpec("general-05", "What does the profile say about the candidate overall?", "general_profile", "GENERAL_SEARCH", ALL_SECTIONS, "General candidate question across all sections."),
    QuerySpec("multi-01", "Summarize all skills and all projects from this profile.", "multi_section", "GENERAL_SEARCH", ("skills", "projects"), "Both requested sections are relevant; no single-section filter is correct."),
    QuerySpec("multi-02", "Give me the candidate's complete work history and education.", "multi_section", "GENERAL_SEARCH", ("experience", "education"), "Requests all memories from experience and education."),
    QuerySpec("multi-03", "What certifications and awards are documented?", "multi_section", "GENERAL_SEARCH", ("certifications", "awards"), "Requests two distinct profile sections."),
    QuerySpec("multi-04", "List every project and publication in the profile.", "multi_section", "GENERAL_SEARCH", ("projects", "publications"), "Requests all evidence from projects and publications."),
    QuerySpec("multi-05", "Summarize education and technical skills together.", "multi_section", "GENERAL_SEARCH", ("education", "skills"), "Requests two sections and therefore a general search."),
    QuerySpec("paraphrase-01", "Trace the candidate's learning path and academic record.", "paraphrased_challenging", "EDUCATION_SEARCH", ("education",), "Paraphrases education without using the section label."),
    QuerySpec("paraphrase-02", "What side initiatives or portfolio builds are described?", "paraphrased_challenging", "PROJECT_SEARCH", ("projects",), "Uses indirect wording for project work."),
    QuerySpec("paraphrase-03", "How does the candidate's career unfold across roles?", "paraphrased_challenging", "EXPERIENCE_SEARCH", ("experience",), "Paraphrases work history as a career progression."),
    QuerySpec("paraphrase-04", "Which formal learning credentials has the candidate earned?", "paraphrased_challenging", "CERTIFICATION_SEARCH", ("certifications",), "Uses credential wording instead of certification."),
]

