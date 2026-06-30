# Kitunga AI

register: product

Kitunga AI est une application de demonstration pour un panier intelligent Fab Lab. Les utilisateurs principaux sont un etudiant qui presente le prototype, un responsable Fab Lab qui gere le catalogue, et un caissier qui valide le panier apres scan du QR code.

Le produit doit montrer un flux credible de bout en bout : detection IA recue par API, ajout automatique au panier, total recalcule, generation de QR code, validation caisse et decrement du stock. L'interface sert la demonstration, elle doit donc etre directe, lisible sur ecran tactile, et assez soignee pour inspirer confiance sans devenir une landing page.

Principes produit :

- Demarrer vite une session panier.
- Montrer clairement les detections acceptees ou ignorees.
- Garder la caisse simple et verifiable.
- Laisser Django Admin gerer le catalogue pendant le MVP.
- Ne pas connecter la Raspberry Pi directement a la base de donnees.
