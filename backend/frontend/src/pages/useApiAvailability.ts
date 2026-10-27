import { useEffect, useState } from "react";
import { api } from "../shared/api";

export function useApiAvailability() {
  const [online, setOnline] = useState(false);
  const [maxSizeMb, setMaxSizeMb] = useState(15);
  useEffect(() => {
    api<{ max_upload_size_mb: number }>("/api/config")
      .then((config) => { setMaxSizeMb(config.max_upload_size_mb); setOnline(true); })
      .catch(() => setOnline(false));
  }, []);
  return { online, maxSizeMb };
}
