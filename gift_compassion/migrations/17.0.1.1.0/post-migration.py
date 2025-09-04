def migrate(cr, version):
    """Link existing gift products to their sponsorship.gift.type."""
    cr.execute(
        """
   UPDATE sponsorship_gift
   SET gift_type_id = sgt.id
   FROM sponsorship_gift_type sgt
   WHERE sponsorship_gift.gift_type = sgt.gmc_gift_type
     AND sponsorship_gift.attribution = sgt.gmc_attribution
     AND
       (sponsorship_gift.sponsorship_gift_type IS NULL OR
        TRIM(sponsorship_gift.sponsorship_gift_type) = '' OR
        sponsorship_gift.sponsorship_gift_type = sgt.gmc_sponsorship_gift_type)
   """
    )
    cr.execute(
        """
UPDATE gift_threshold_settings
SET gift_type_id = sgt.id
FROM sponsorship_gift_type sgt
WHERE gift_threshold_settings.gift_type = sgt.gmc_gift_type
  AND gift_threshold_settings.gift_attribution = sgt.gmc_attribution
  AND (
        gift_threshold_settings.sponsorship_gift_type IS NULL OR
        TRIM(gift_threshold_settings.sponsorship_gift_type) = '' OR
    gift_threshold_settings.sponsorship_gift_type = sgt.gmc_sponsorship_gift_type)
        """
    )
