# LabGym Zoo

The LabGym Zoo contains pre-trained Detector and Categorizer models as well as behavior examples that were used to train these models. You can use pre-trained models to develop your own models with much less data, leveraging the benefits of transfer learning. You can also use the behavior examples as benchmarking datasets to develop, refine and evaluate tools. We hope that the LabGym Zoo helps to foster collaborative dialogues in the community. We also envision that teachers and students will use the database for education in behavioral analysis. Instructions on how to contribute to the LabGym Zoo will be added soon.

<p>&nbsp;</p>

## Detector Models

All the trained Detectors are stored in '../LabGym/detectors/'. Use `pip show LabGym` to find where '../LabGym/' folder locates in your computer. Copy the folder of a Detector to '../LabGym/detectors/' and access it from LabGym GUI. 

Coming soon!

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

<p>&nbsp;</p>

## Behavior Examples

| Name             | Description | Source |
|------------------|-----------|--------|
| [Larvae nociception](https://drive.google.com/file/d/1q4KfML2-uiHrD3du2qKoSR0sW2Nbk5XS/view?usp=sharing) | Used to train 'Larva_Nociception_TopView_30fps' | [Hu et al 2023.](https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7) |
| [Mouse home cage](https://drive.google.com/file/d/1xaUBTrJ4v0xGCQCEgh4tZ7fOOJr6_nMP/view?usp=sharing) | Used to train 'Mouse_NonSocial_SideView_30fps' | [Hu et al 2023.](https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7) |
| [Rat psychomotor activity](https://drive.google.com/file/d/1l2fY6Ycg8f6DdUfUEymuIfk7Hn9Bh2sr/view?usp=sharing) | Used to train 'Rat_NonSocial_TopView_30fps' | [Hu et al 2023.](https://www.cell.com/cell-reports-methods/fulltext/S2667-2375(23)00026-7) |
| [5-fly courtship preference](https://drive.google.com/file/d/1VGCyhvgGyoT_5P8uNHC1xJq8jX75a_K5/view?usp=sharing) | Used to train 'Fly_CourtshipPreference_TopView_25fps' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [One mouse two boxes](https://drive.google.com/file/d/1PPCNyHlTYSijU0AqQOIpsfKyNyvOhP_l/view?usp=sharing) | Used to train 'Mouse_SocialRecognition_TopView_15fps' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |
| [Two voles](https://drive.google.com/file/d/15EMsQyS1ZH12UsvrakPufeL8t24MQ7xv/view?usp=sharing) | Used to train 'Vole_PairBound_TopView_30fps' | [Goss et al 2024.](https://www.biorxiv.org/content/10.1101/2024.07.07.602350v1) |

