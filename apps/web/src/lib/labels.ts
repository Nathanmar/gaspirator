import type { SupplierType } from "@/features/auth/auth-api";

export const SUPPLIER_TYPE_LABELS: Record<SupplierType, string> = {
	canteen: "Cantine",
	hospital: "Hôpital",
	supermarket: "Supermarché",
	other: "Autre",
};
