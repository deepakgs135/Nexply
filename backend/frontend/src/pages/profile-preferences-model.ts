export type Preferences = {
  current_ctc: string; expected_ctc: string; expected_ctc_range: string; minimum_expected_ctc: string;
  currency: string; preferred_locations: string[]; preferred_job_titles: string[]; work_mode: string;
  employment_types: string[]; notice_period: string; availability: string;
  willing_to_relocate: boolean | null; preferred_industries: string[];
};

export const EMPTY_PREFERENCES: Preferences = {
  current_ctc: "", expected_ctc: "", expected_ctc_range: "", minimum_expected_ctc: "", currency: "INR",
  preferred_locations: [], preferred_job_titles: [], work_mode: "", employment_types: [], notice_period: "",
  availability: "", willing_to_relocate: null, preferred_industries: [],
};

export const joined = (value: unknown) => Array.isArray(value)
  ? value.filter((item): item is string => typeof item === "string").join(", ") : "";
