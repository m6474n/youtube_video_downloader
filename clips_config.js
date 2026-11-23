// clips_config.js — Configuration for download-clips
module.exports = {
  // YouTube video or stream URL
  url: "https://www.youtube.com/watch?v=AwH8ZpGo69Y&t=5s",

  // Preferred quality: "best", "1080p", "720p", "480p", or "audio"
  quality: "best",

  // Output folder (defaults to user's system Downloads folder)
  output_dir: "~/Downloads",

  // Clips with original start points + 3-minute extended end points
  clips: [
    {
      name: "who_is_my_real_dad",
      start: "00:19:08",
      end: "00:22:08",
    },
    {
      name: "5g_speed_test_and_theft",
      start: "02:16:58",
      end: "02:19:58",
    },
    {
      name: "modern_library_philosophy",
      start: "02:17:11",
      end: "02:20:11",
    },
    {
      name: "total_heist_disaster",
      start: "03:46:47",
      end: "03:49:47",
    },
    {
      name: "tomi_versetti_theory",
      start: "07:10:08",
      end: "07:13:08",
    },
    {
      name: "appreciating_virtual_drink",
      start: "07:53:12",
      end: "07:56:12",
    },
    {
      name: "pubg_mobile_flash_sponsor",
      start: "08:23:06",
      end: "08:26:06",
    },
    {
      name: "gym_fitness_routine",
      start: "08:43:23",
      end: "08:46:23",
    },
    {
      name: "gentleman_gym_workout",
      start: "08:51:18",
      end: "08:54:18",
    },
    {
      name: "lawyer_call_and_blown_cover",
      start: "09:14:31",
      end: "09:17:31",
    },
    {
      name: "parking_alignment_fails",
      start: "09:58:34",
      end: "10:01:34",
    },
    {
      name: "rich_kid_sociological_rant",
      start: "10:29:26",
      end: "10:32:26",
    },
    {
      name: "security_detail_confusion",
      start: "10:37:02",
      end: "10:40:02",
    },
    {
      name: "failed_stealth_rant",
      start: "10:57:18",
      end: "11:00:18",
    },
    {
      name: "final_giveaway_event",
      start: "11:18:01",
      end: "11:21:01",
    },
  ],
};
