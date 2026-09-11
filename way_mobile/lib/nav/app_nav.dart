import 'package:flutter/foundation.dart';

/// Cross-tab navigation for MainScreen (Home / Profile / Add / Wallet).
class AppNav {
  /// Bottom nav index: 0 Home, 1 Profile, 2 Add Ticket, 3 Wallet
  static final ValueNotifier<int> tabIndex = ValueNotifier<int>(0);

  /// Bump to force HomeScreen to reload active journey.
  static final ValueNotifier<int> homeRefreshTick = ValueNotifier<int>(0);

  /// ✅ Notify when profile is updated (name, email, etc.)
  static final ValueNotifier<int> profileUpdated = ValueNotifier<int>(0);

  /// ✅ Notify when a ticket is activated (journey started)
  /// This triggers refresh in My Trips and My Stats screens
  static final ValueNotifier<int> ticketActivated = ValueNotifier<int>(0);

  static void goHomeAndRefresh() {
    tabIndex.value = 0;
    homeRefreshTick.value++;
  }

  /// ✅ Notify all screens that profile has been updated
  static void notifyProfileUpdated() {
    profileUpdated.value++;
  }

  /// ✅ Notify all screens that a ticket was activated
  /// My Trips and My Stats will refresh automatically
  static void notifyTicketActivated() {
    ticketActivated.value++;
  }
}
