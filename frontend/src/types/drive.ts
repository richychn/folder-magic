export type DriveFileNode = {
  id: string;
  name: string;
  parent_id?: string | null;
  description?: string | null;
};

export type DriveFolderNode = {
  id: string;
  name: string;
  parent_id?: string | null;
  description?: string | null;
  children_folders: DriveFolderNode[];
  files: DriveFileNode[];
};

// Types used by DriveList component
export type DriveFile = {
  id: string;
  name: string;
  size?: string;
  modifiedTime?: string;
  webViewLink?: string;
};

export type DriveFolder = {
  id: string;
  name: string;
  webViewLink?: string;
};

export type Diff = {
  action_type: string;
  file_id: string;
  parent_id: string;
  name: string;
}

export type DiffList = {
  actions: Diff[]
}

// Type for the API response from /api/drive/structure
export type DriveStructureResponse = {
  current_structure: DriveFolderNode | null;
  proposed_structure: DriveFolderNode | null;
  diff_list: DiffList | null;
};
