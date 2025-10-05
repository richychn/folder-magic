export type DriveFolder = {
  id: string;
  name: string;
  mimeType?: string;
  iconLink?: string;
  webViewLink?: string;
};

export type DriveFile = {
  id: string;
  name: string;
  mimeType?: string;
  modifiedTime?: string;
  size?: string;
  iconLink?: string;
  webViewLink?: string;
};

export type DriveChildrenResponse = {
  folderId: string;
  folders: DriveFolder[];
  files: DriveFile[];
};
