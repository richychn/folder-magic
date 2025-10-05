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
