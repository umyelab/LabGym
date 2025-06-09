# LabGym Zoo

The LabGym Zoo contains pre-trained Detector and Categorizer models as well as behavior examples that were used to train these models. You can use pre-trained models to develop your own models with much less data, leveraging the benefits of transfer learning. You can also use the behavior examples as benchmarking datasets to develop, refine and evaluate tools. We hope that the LabGym Zoo helps to foster collaborative dialogues in the community. We also envision that teachers and students will use the database for education in behavioral analysis. Instructions on how to contribute to the LabGym Zoo will be added soon.

The dataset generated in [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) for testing the Categorizer performance has been published in Zenodo (DOI: 10.5281/zenodo.15420233).

<p>&nbsp;</p>

## Detector Models

All the trained Detectors are stored in '../LabGym/detectors/'. Use `pip show LabGym` to find where '../LabGym/' folder locates in your computer. Copy the folder of a Detector to '../LabGym/detectors/' and access it from LabGym GUI. 

| Name             | Description | Source |
|------------------|-----------|--------|
| [MouseBoxes_TopView_960](https://drive.google.com/file/d/1EYPS-EO7kzH_eMnwKZGdWyDH1Eu2t34H/view?usp=sharing) | Detecting a mouse interacting with two boxes | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [MacaqueInField_FrontView_960](https://drive.google.com/file/d/1keX4wY3hPuf7RZQ4_WXi8tzvE0Oeabw7/view?usp=sharing) | Detecting macaques in the field | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [VolePaired_TopView_800](https://drive.google.com/file/d/1JcdQ3I7MZZ5XGqSzTbwqpWpyitmshYjv/view?usp=sharing) | Detecting two interacting voles | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Fly_TopView_640_01](https://drive.google.com/file/d/1PRHeSY3Kd8FUQSY_Yvm-LuP6-FWJKKxQ/view?usp=sharing) | Detecting 5 interacting flies with 0 ID switching, dedicated to [this video](https://drive.google.com/file/d/1I-bSz-PUzKHEJ1jKqknxs5PtceLKuxBv/view?usp=sharing) | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Fly_TopView_640_02](https://drive.google.com/file/d/1woNsroKPDlxqnyTlDV-YrBWw7YcHFfHq/view?usp=sharing) | Detecting 5 interacting flies with 0 ID switching, dedicated to [this video](https://drive.google.com/file/d/17LAbc0SyudmfGrU6uzOR7mI2cuahNUgU/view?usp=sharing) | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Fly_TopView_640_03](https://drive.google.com/file/d/1xU0dVjebZdKyH3jBYJG-dowxHdxYQNh6/view?usp=sharing) | Detecting 5 interacting flies with 0 ID switching, dedicated to [this video](https://drive.google.com/file/d/1Qcht6vOyuJhZyIfX2e5jYNjucblFVtzn/view?usp=sharing) | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Fly_TopView_640_04](https://drive.google.com/file/d/1Ob1x5s5MVRIOwhf5p40L2kJL-0f_mp_d/view?usp=sharing) | Detecting 5 interacting flies with 0 ID switching, dedicated to [this video](https://drive.google.com/file/d/1781zrL2j2m5t3dVPfE4pht0zHB5c3ziq/view?usp=sharing) | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Fly_TopView_640_05](https://drive.google.com/file/d/1e_gnBE1XmhAYrq339851mRi3MqAbNud8/view?usp=sharing) | Detecting 5 interacting flies with 0 ID switching, dedicated to [this video](https://drive.google.com/file/d/1lp7ckzeNGyLhiYkoVfP7HMePfxtUyf62/view?usp=sharing) | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Fly_TopView_640_06](https://drive.google.com/file/d/1D0AbXVj7cWOeBh3lVuPDjJVNib_WDPrG/view?usp=sharing) | Detecting 5 interacting flies with 0 ID switching, dedicated to [this video](https://drive.google.com/file/d/1ecgUnFwLLAYEsQNnsj16OcwQTdku3vQt/view?usp=sharing) | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Fly_TopView_640_07](https://drive.google.com/file/d/1hfCU-kV-VSralmy76qsjYjzYmGl7ryzj/view?usp=sharing) | Detecting 5 interacting flies with 0 ID switching, dedicated to [this video](https://drive.google.com/file/d/16EbqC-QOPLfwaF6xbW0dvT-NPlqNDabw/view?usp=sharing) | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Fly_TopView_640_08](https://drive.google.com/file/d/1_U-i9DbXVGMhop3NAtUrRX58uWo-sT2R/view?usp=sharing) | Detecting 5 interacting flies with 0 ID switching, dedicated to [this video](https://drive.google.com/file/d/1AfLG3WE9MTyJKeGqnooDmpafuyNJ-EbN/view?usp=sharing) | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Fly_TopView_640_09](https://drive.google.com/file/d/1U6Y9A11AuwrEEsTAp22o-jNmFWMSJSVJ/view?usp=sharing) | Detecting 5 interacting flies with 0 ID switching, dedicated to [this video](https://drive.google.com/file/d/1CK_K8K2ULqeZ9mQYo1ZaVXFHSsXKstQV/view?usp=sharing) | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Fly_TopView_640_10](https://drive.google.com/file/d/1sHRWi3FCuW-ayjwMtuILvAO8A4pjvJrp/view?usp=sharing) | Detecting 5 interacting flies with 0 ID switching, dedicated to [this video](https://drive.google.com/file/d/1SUxojWr7lsCMMRAzkSUBn601tQzY1CwW/view?usp=sharing) | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Fly_TopView_640_11](https://drive.google.com/file/d/15dUoPBYl1ORTmnJPLAqf3DfW46O5x71v/view?usp=sharing) | Detecting 5 interacting flies with 0 ID switching, dedicated to [this video](https://drive.google.com/file/d/17H_PZJuHX5dEdRSTA3PXHhYPcwyi68i1/view?usp=sharing) | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Fly_TopView_640_12](https://drive.google.com/file/d/1gnhviMCvncE3AlXc8hd_bHIV-fT1SAIA/view?usp=sharing) | Detecting 5 interacting flies with 0 ID switching, dedicated to [this video](https://drive.google.com/file/d/1TQ3-W5KBFbYSHS4AX0t3uxMDLXz-vJtP/view?usp=sharing) | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |

<p>&nbsp;</p>

## Image Examples (used to train Detector Models)

| Name             | Description | Source |
|------------------|-----------|--------|
| [One mouse two boxes](https://drive.google.com/file/d/1OpLOo-2YAGXr86_NZuRN2oFgDiXtVYqO/view?usp=sharing) | Used to train 'MouseBoxes_TopView_960' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Macaques in the field](https://drive.google.com/file/d/1Ydv1jO0RiK92cd2xPlLmmkEGQGgT-GdI/view?usp=sharing) | Used to train 'MacaqueInField_FrontView_960' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [5 flies 01](https://drive.google.com/file/d/1nR6LSzWnMuwDea_aBcRRg3OedA9UUmbA/view?usp=sharing) | Used to train 'Fly_TopView_640_01' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [5 flies 02](https://drive.google.com/file/d/1wgASMuhxNfwLbQNdQlqIJ645yKGGjqas/view?usp=sharing) | Used to train 'Fly_TopView_640_02' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [5 flies 03](https://drive.google.com/file/d/1n-JJdUbPJxa5q6DM1P-F7CEW_88So-P9/view?usp=sharing) | Used to train 'Fly_TopView_640_03' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [5 flies 04](https://drive.google.com/file/d/1XNCNkJqyTIKchUO7n5mSxr6H3mU3CWYL/view?usp=sharing) | Used to train 'Fly_TopView_640_04' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [5 flies 05](https://drive.google.com/file/d/1QiGDK40IS75zdS956wD6p20LD0CoWfB3/view?usp=sharing) | Used to train 'Fly_TopView_640_05' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [5 flies 06](https://drive.google.com/file/d/12yRV4-jBlyV_umfbcJnzQHx9oJQXFJfK/view?usp=sharing) | Used to train 'Fly_TopView_640_06' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [5 flies 07](https://drive.google.com/file/d/1NNoj8no7DySI9_uSYTHb4r49A_t4UZ0Q/view?usp=sharing) | Used to train 'Fly_TopView_640_07' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [5 flies 08](https://drive.google.com/file/d/1sa8uzsLIz1iHaJ3t3TP9Z4CnNx2J012J/view?usp=sharing) | Used to train 'Fly_TopView_640_08' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [5 flies 09](https://drive.google.com/file/d/10xK-Lnz6Ubg_dWVLht8-9ff9tiIgSE37/view?usp=sharing) | Used to train 'Fly_TopView_640_09' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [5 flies 10](https://drive.google.com/file/d/1_hGbXQ9Ydbrj8id04VIzymfMBatIqM3p/view?usp=sharing) | Used to train 'Fly_TopView_640_10' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [5 flies 11](https://drive.google.com/file/d/19iNXDAs42FkJco7ex6Tp8dqkLJ-KG0YK/view?usp=sharing) | Used to train 'Fly_TopView_640_11' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [5 flies 12](https://drive.google.com/file/d/1evhT_iNWt85AHs0hjFZFLQyKr6yW2Ehq/view?usp=sharing) | Used to train 'Fly_TopView_640_12' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |

<p>&nbsp;</p>

## Categorizer Models

All the trained Categorizers are stored in '../LabGym/models/'. Use `pip show LabGym` to find where '../LabGym/' folder locates in your computer. Copy the folder of a Categorizer to '../LabGym/models/' and access it from LabGym GUI.

| Name             | Description | Source |
|------------------|-----------|--------|
| [Larva_Nociception_TopView_30fps](https://drive.google.com/file/d/1ITz9aBR8LEbi0RKsoPCTeRvvEnRYitUR/view?usp=sharing) | Categorizing 6 larva behaviors in response to painful stimuli | [Hu et al 2023.](https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7) |
| [Mouse_NonSocial_SideView_30fps](https://drive.google.com/file/d/13ss-5myp0du6pXzbueKRMb__8VG0kW-Y/view?usp=sharing) | Categorizing 20 mouse behaviors in a home cage | [Hu et al 2023.](https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7) |
| [Rat_NonSocial_TopView_30fps](https://drive.google.com/file/d/1myHhpScuKRPPUk-7tY01789CAwKJjrux/view?usp=sharing) | Categorizing 8 rat behaviors in psychomotor activity | [Hu et al 2023.](https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7) |
| [Fly_CourtshipPreference_TopView_25fps](https://drive.google.com/file/d/1j0LOSi3H0cNiHbedMz6gGfx2_-K0JKyM/view?usp=sharing) | Categorizing 6 fly behaviors in 5-fly courtship preference assay | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Mouse_SocialRecognition_TopView_15fps](https://drive.google.com/file/d/1jBJq--yPdVitFEUjGajEZdgOMoZdB9LE/view?usp=sharing) | Categorizing 9 mouse behaviors in mouse-boxes interactions | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Vole_PairBound_TopView_30fps](https://drive.google.com/file/d/1x_wLN494PEILFOAXcgyW4xhssiU4U1W3/view?usp=sharing) | Categorizing 9 vole behaviors in two-vole interactions | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Macaque_SocialGroom_FrontView_25fps](https://drive.google.com/file/d/1JNzZC0YvFUUshwvLNoC-pYbY4R7PcMBa/view?usp=sharing) | Categorizing 3 macaque behaviors in their social interactions in the field | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |

<p>&nbsp;</p>

## Behavior Examples (used to train Categorizer Models)

| Name             | Description | Source |
|------------------|-----------|--------|
| [Larvae nociception](https://drive.google.com/file/d/1q4KfML2-uiHrD3du2qKoSR0sW2Nbk5XS/view?usp=sharing) | Used to train 'Larva_Nociception_TopView_30fps' | [Hu et al 2023.](https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7) |
| [Mouse home cage](https://drive.google.com/file/d/1xaUBTrJ4v0xGCQCEgh4tZ7fOOJr6_nMP/view?usp=sharing) | Used to train 'Mouse_NonSocial_SideView_30fps' | [Hu et al 2023.](https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7) |
| [Rat psychomotor activity](https://drive.google.com/file/d/1l2fY6Ycg8f6DdUfUEymuIfk7Hn9Bh2sr/view?usp=sharing) | Used to train 'Rat_NonSocial_TopView_30fps' | [Hu et al 2023.](https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7) |
| [5-fly courtship preference](https://drive.google.com/file/d/1VGCyhvgGyoT_5P8uNHC1xJq8jX75a_K5/view?usp=sharing) | Used to train 'Fly_CourtshipPreference_TopView_25fps' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [One mouse two boxes](https://drive.google.com/file/d/1PPCNyHlTYSijU0AqQOIpsfKyNyvOhP_l/view?usp=sharing) | Used to train 'Mouse_SocialRecognition_TopView_15fps' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Two voles](https://drive.google.com/file/d/15EMsQyS1ZH12UsvrakPufeL8t24MQ7xv/view?usp=sharing) | Used to train 'Vole_PairBound_TopView_30fps' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Macaques in the field](https://drive.google.com/file/d/1Y7MgBWpffNYE4d6gHeXeHikchg5RL_u9/view?usp=sharing) | Used to train 'Macaque_SocialGroom_FrontView_25fps' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
