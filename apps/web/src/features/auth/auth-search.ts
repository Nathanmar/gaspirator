import { z } from "zod";

/**
 * Search params of the auth pages: `?role=` is the audience chosen on the landing page
 * (`OrganizationType` of the contract). An unknown value is dropped instead of breaking the page.
 */
export const authSearchSchema = z.object({
	role: z.enum(["supplier", "association"]).optional().catch(undefined),
});
