"use client";

export interface ComplianceDocumentCapabilities {
  canRead: boolean;
  canCreate: boolean;
  canUpdate: boolean;
  canApprove: boolean;
  canActivate: boolean;
  canArchive: boolean;
}

export function mapComplianceDocumentCapabilities(
  hasPermission: (permission: string) => boolean,
): ComplianceDocumentCapabilities {
  return {
    canRead: hasPermission("compliance_document:read"),
    canCreate: hasPermission("compliance_document:create"),
    canUpdate: hasPermission("compliance_document:update"),
    canApprove: hasPermission("compliance_document:approve"),
    canActivate: hasPermission("compliance_document:activate"),
    canArchive: hasPermission("compliance_document:archive"),
  };
}
