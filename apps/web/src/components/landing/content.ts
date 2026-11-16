export const NAV_LINKS = [
  { href: "#constat", label: "Constat" },
  { href: "#circuit", label: "Circuit" },
  { href: "#acteurs", label: "Acteurs" },
] as const;

// `role` uses the `OrganizationType` values of the API contract so the login page can open on the
// right audience and pass it on to the registration form.
export const JOIN_LINKS = [
  { href: "/login?role=supplier", label: "Je suis fournisseur", tone: "lime" },
  { href: "/login?role=association", label: "Je suis une association", tone: "tomato" },
] as const;

/** Words wrapped in asterisks are set in the accent serif. */
export const MANIFESTO =
  "Gaspirator *aspire* le surplus des cantines, des hôpitaux et des supermarchés, puis le redirige vers les *associations* qui en ont besoin. Avant qu'il ne soit trop tard.";

export const STEPS = [
  {
    index: "01",
    title: "Publier",
    actor: "Fournisseur",
    text: "Le fournisseur publie son surplus : produits, quantités, date limite et créneau de retrait.",
  },
  {
    index: "02",
    title: "Réserver",
    actor: "Association",
    text: "Les associations proches le voient sur Gaspirator et le réservent en un geste.",
  },
  {
    index: "03",
    title: "Récupérer",
    actor: "Association",
    text: "Un code de retrait unique est remis à l'association, qui vient chercher le don.",
  },
  {
    index: "04",
    title: "Confirmer",
    actor: "Fournisseur",
    text: "Le fournisseur saisit le code : la remise est confirmée et l'historique se met à jour.",
  },
] as const;

export const AUDIENCES = [
  {
    id: "fournisseurs",
    eyebrow: "Fournisseurs",
    title: "Vous avez du surplus.",
    who: "Cantines, hôpitaux, supermarchés, traiteurs.",
    features: [
      "Publier un don en quelques clics",
      "Valider chaque retrait par code",
      "Suivre l'historique des dons",
      "Exporter un bilan de vos dons",
    ],
    tone: "lime",
  },
  {
    id: "associations",
    eyebrow: "Associations",
    title: "Vous avez des repas à servir.",
    who: "Banques alimentaires, épiceries solidaires, maraudes.",
    features: [
      "Trouver les fournisseurs proches",
      "Filtrer les dons disponibles",
      "Réserver et récupérer avec un code",
      "Échanger avec le fournisseur",
    ],
    tone: "tomato",
  },
] as const;

// Demo data for the "Réserver" map: an association near Bellecour and real places around it in
// Lyon that could donate. Portions are made up; distances are as the crow flies from the association.
export const RESERVE_ORIGIN: [number, number] = [4.832, 45.7578];

export interface Supplier {
  id: string;
  name: string;
  /** Label on the map pin. */
  shortName: string;
  lngLat: [number, number];
  distance: string;
  portions: number;
}

export const SUPPLIERS: Supplier[] = [
  {
    id: "halles-bocuse",
    name: "Halles de Lyon Paul Bocuse",
    shortName: "Halles Bocuse",
    lngLat: [4.8505, 45.763],
    distance: "1,6 km",
    portions: 38,
  },
  {
    id: "saint-joseph-saint-luc",
    name: "Hôpital Saint-Joseph Saint-Luc",
    shortName: "Saint-Joseph Saint-Luc",
    lngLat: [4.8412, 45.7488],
    distance: "1,2 km",
    portions: 27,
  },
  {
    id: "croix-rousse",
    name: "Hôpital de la Croix-Rousse",
    shortName: "Hôpital Croix-Rousse",
    lngLat: [4.8277, 45.7824],
    distance: "2,8 km",
    portions: 45,
  },
  {
    id: "lycee-du-parc",
    name: "Lycée du Parc",
    shortName: "Lycée du Parc",
    lngLat: [4.853, 45.7702],
    distance: "2,1 km",
    portions: 33,
  },
  {
    id: "edouard-herriot",
    name: "Hôpital Édouard-Herriot",
    shortName: "Édouard-Herriot",
    lngLat: [4.8813, 45.7428],
    distance: "4,2 km",
    portions: 64,
  },
  {
    id: "carrefour-confluence",
    name: "Carrefour Lyon Confluence",
    shortName: "Carrefour Confluence",
    lngLat: [4.8163, 45.7413],
    distance: "2,2 km",
    portions: 52,
  },
];
