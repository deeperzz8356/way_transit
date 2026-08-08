import 'package:flutter/foundation.dart';

/// Cross-tab navigation for MainScreen (Home / Profile / Add / Wallet).
class AppNav {
  /// Bottom nav index: 0 Home, 1 Profile, 2 Add Ticket, 3 Wallet
  static final ValueNotifier<int> tabIndex = ValueNotifier<int>(0);

  /// Bump to force HomeScreen to reload active journey.
  static final ValueNotifier<int> homeRefreshTick = ValueNotifier<int>(0);

  static void goHomeAndRefresh() {
    tabIndex.value = 0;
    homeRefreshTick.value++;
  }
}
