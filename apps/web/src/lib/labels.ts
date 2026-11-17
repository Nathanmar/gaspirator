import type { Storage } from "@/features/association/association-api";
import type { SupplierType } from "@/features/auth/auth-api";

export const STORAGE_LABELS: Record<Storage, string> = {
	ambient: "Ambiant",
	refrigerated: "Réfrigéré",
	frozen: "Surgelé",
};

export const SUPPLIER_TYPE_LABELS: Record<SupplierType, string> = {
	canteen: "Cantine",
	hospital: "Hôpital",
	supermarket: "Supermarché",
	other: "Autre",
};
