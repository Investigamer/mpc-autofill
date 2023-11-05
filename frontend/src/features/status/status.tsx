import React from "react";

import { SelectedImagesStatus } from "@/features/status/bulkManagementStatus";
import { MobileStatus } from "@/features/status/mobileStatus";
import { ProjectStatus } from "@/features/status/projectStatus";

export function Status() {
  return (
    <>
      <h2>Edit Project</h2>
      <MobileStatus />
      <SelectedImagesStatus />
      <ProjectStatus />
    </>
  );
}
