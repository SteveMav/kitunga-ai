# Mapping labels YOLO vers produits Django

Le modele YOLO utilise les labels bruts venant du projet d'entrainement :

```text
C:\dev\makers\training detection model\data_t\ElectroCom-61_v2\data.yaml
```

Dans Django, les produits utilisent des labels simples en snake_case dans `Product.detection_label`.

Regle appliquee :

```text
Servo-Motor -> servo_motor
Sonar-Sensor -> sonar_sensor
Arduino-Uno -> arduino_uno
```

## Exemples importants

| Label modele YOLO | Label Django simple | Produit affiche |
| --- | --- | --- |
| `Arduino-Uno` | `arduino_uno` | Arduino Uno |
| `ESP32` | `esp32` | ESP32 DevKit |
| `Breadboard` | `breadboard` | Breadboard 830 points |
| `Relay-Module` | `relay_module` | Module relais |
| `Servo-Motor` | `servo_motor` | Servo moteur SG90 |
| `Sonar-Sensor` | `sonar_sensor` | Capteur ultrason HC-SR04 |

## Synchroniser la base avec le modele

Lance cette commande depuis la racine du backend :

```powershell
.\.venv\Scripts\python.exe manage.py sync_model_catalog
```

Elle cree ou met a jour un produit pour chaque classe du modele YOLO. Elle renomme aussi les anciens labels de demo :

| Ancien label | Nouveau label |
| --- | --- |
| `breadboard_830` | `breadboard` |
| `esp32_devkit` | `esp32` |
| `hc_sr04` | `sonar_sensor` |
| `relay_module_1ch` | `relay_module` |
| `servo_sg90` | `servo_motor` |

Note : la base locale peut contenir `dupont_wires` en plus. C'est un produit de demo manuel, mais il n'est pas detecte par le modele ElectroCom-61 actuel.
