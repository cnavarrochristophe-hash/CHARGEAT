import "./globals.css";

export const metadata = {
  title: "Charge & Eat",
  description: "Bornes rapides + restaurants accessibles à pied",
};

export default function RootLayout({ children }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
