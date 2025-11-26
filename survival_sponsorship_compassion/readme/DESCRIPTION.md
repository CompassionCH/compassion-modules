This module add :

- New type *CSP* for sponsorships  
  - Filter the product available

- Survival Sponsorship Sale on the product.template  
  - Define if the product is actually used for the survival sponsorships

- Specific monitoring fields for product.product  
  - Survival Field Office : Which field office this product applies to
  - Slot used : Number of intervention slot already taken
  - Survival Slots : Number of slots available for this field office
  - Survival Sponsorship : Number of sponsorships active
  - Alltime Survival Sponsorship : Number of sponsorships on this
    specific product (active and inactive)

- Base automation that will trigger schedule activities  
  - Put a schedule activity on the products that has too much slot used
    (by default defined at 80%+)
