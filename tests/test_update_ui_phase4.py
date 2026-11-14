"""Rendered System Update and cross-page state regressions for Part 4.

The Node fixture executes the shipped renderer with a small DOM stub. It does
not claim screenshot, layout, browser-engine, Docker or live-service coverage.
"""
import json
import shutil
import subprocess

import pytest

from romarr import ui


def _node(script: str, payload: dict) -> str:
    """Run first-party UI logic in Node without a network or application server."""
    node = shutil.which("node")
    if not node:
        pytest.skip("Node unavailable; rendered UI regression not executed")
    result = subprocess.run(
        [node, "-e", script, json.dumps(payload)],
        capture_output=True, text=True, timeout=25, check=False,
    )
    assert result.returncode == 0, result.stderr[:1600]
    return result.stdout.strip()


def _helpers() -> str:
    """Select exactly the installed shared presentation helpers."""
    start = ui.JS.index("/* Present only verified backend identity")
    stop = ui.JS.index("RENDER.stats=async()=>", start)
    return ui.JS[start:stop]


_BASE = r"""
const data=JSON.parse(process.argv[1]);
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const root={innerHTML:''}, controls={};
const RENDER={};
const j=async()=>data;
const $=selector=>{
  if(selector==='#page')return root;
  if(['#up-check','#up-apply','#up-plugins'].includes(selector)
      &&!root.innerHTML.includes('id="'+selector.slice(1)+'"'))return null;
  return controls[selector]||(controls[selector]={
    innerHTML:'',textContent:'',onclick:null,disabled:false
  });
};
const toast=()=>{},go=()=>{},confirm=()=>false;
"""


def _update(payload: dict) -> dict:
    """Execute the real Update renderer, including its conditional controls."""
    start = ui.JS.index("let updatePollGeneration=0;")
    stop = ui.JS.index("RENDER.logs=async()=>", start)
    script = (_BASE + _helpers() + ui.JS[start:stop] + """
RENDER.update().then(()=>console.log(JSON.stringify({
  html:root.innerHTML,
  check_bound:typeof controls['#up-check']?.onclick==='function'
}))).catch(e=>{console.error(String(e));process.exitCode=1;});
""")
    return json.loads(_node(script, payload))


def _stats_banner(stats: dict, update: dict | None) -> str:
    """Render the shared Stats update banner independently of charts/actions."""
    script = (_BASE + _helpers() + """
console.log(JSON.stringify(statsUpdateMessage(data.stats,data.update)));
""")
    return json.loads(_node(script, {"stats": stats, "update": update}))


def _payload(**overrides) -> dict:
    """Supply conservative, version-pinned API response fixtures."""
    result = {
        "running_version": "1.8.1",
        "latest_version": "1.8.2",
        "update_available": False,
        "check_status": {"state": "never_checked"},
        "install": {"kind": "docker", "can_apply": False},
        "settings": {
            "auto_update": True, "auto_update_effective": False,
            "update_check": True, "update_channel": "stable",
        },
        "plugins": {}, "docker_guidance": ["Review host deployment."],
        "update_log": "",
    }
    result.update(overrides)
    return result


@pytest.mark.parametrize("state,label", [
    ("current", "no"), ("never_checked", "not checked"),
    ("unknown", "unknown"), ("error", "error"),
])
def test_update_page_renders_each_nonavailable_verdict(state, label):
    """A false Boolean alone must never mean a successful current check."""
    html = _update(_payload(check_status={"state": state}))["html"]
    headings = {
        "current": "You're up to date",
        "never_checked": "Not checked yet",
        "unknown": "Update status unknown",
        "error": "Couldn't check for updates",
    }
    assert '<h2 id="update-status-heading">' + headings[state] + '</h2>' in html
    assert "<dt>Last known release</dt>" in html or state == "current"


def test_update_page_available_uses_positive_check_not_legacy_boolean():
    """A validated available state drives the tile, not a cached Boolean."""
    html = _update(_payload(check_status={"state": "available"},
                            update_available=False))["html"]
    assert '<h2 id="update-status-heading">Update available</h2>' in html
    assert '<div class="update-version is-new">' in html
    assert "<dt>Latest on GitHub</dt>" in html


def test_update_page_docker_configured_is_not_effective():
    """A saved preference never authorizes an in-container Docker update."""
    result = _update(_payload(check_status={"state": "available"}))
    html = result["html"]
    assert "ROMarr cannot update its own Docker image." in html
    assert 'id="up-check"' in html and result["check_bound"]
    assert 'id="up-apply"' not in html


def test_update_page_git_eligible_keeps_manual_action():
    """Keep the original Update now action for capable Git installations."""
    html = _update(_payload(
        check_status={"state": "available"},
        install={"kind": "git", "can_apply": True},
        settings={"auto_update": True, "auto_update_effective": True},
    ))["html"]
    assert "Installs eligible updates after a scheduled check." in html
    assert 'id="up-apply"' in html


def test_update_page_legacy_absence_is_honest():
    """Older APIs with no check/capability/build fields must not claim current."""
    result = _update({"running_version": "0.0.0+unknown",
                      "install": {"kind": "none"}})
    html = result["html"]
    assert '<h2 id="update-status-heading">Update status unknown</h2>' in html
    assert "Build type <b>Unknown</b>" in html
    assert result["check_bound"]


def test_update_page_escapes_identity_and_preserves_optional_sections():
    """Neither untrusted source identity nor plugin/log data may become markup."""
    html = _update(_payload(
        build={"type": "development", "source_ref": "refs/heads/<img src=x>",
               "source_revision": "f" * 40, "source_repository": "foo/bar"},
        plugins={"<img>": {"source": "<script>", "ref": "main"}},
        update_log="<script>alert(1)</script>",
    ))["html"]
    assert "&lt;img&gt;" in html and "<img src=x>" not in html
    assert "&lt;script&gt;" in html and "<script>" not in html
    assert "ROM Hub plugins" in html and "Last self-update log" in html
    assert 'id="up-plugins"' in html


def test_update_page_plugin_sections_are_conditional():
    """Keep the maintainer's plugin table and action hidden when empty."""
    empty = _update(_payload(plugins={}))["html"]
    assert "Auto-update ROM Hub plugins" in empty
    assert 'id="up-plugins"' not in empty
    assert 'id="update-plugins-heading"' not in empty

    installed = _update(_payload(plugins={
        "sample": {"source": "example/repo", "ref": "main",
                   "commit": "abcdef1234567890"},
    }))["html"]
    assert 'id="up-plugins"' in installed
    assert 'id="update-plugins-heading"' in installed
    for heading in ("Plugin", "Source", "Ref", "Commit"):
        assert '<th>' + heading + '</th>' in installed
    assert "abcdef12" in installed


def test_update_page_check_timestamp_and_disclosure_sections():
    """Use the stored successful check, not an invented preview timestamp."""
    state = _payload(check_status={
        "state": "available", "last_success_at": "2026-11-13T10:30:00Z",
    })
    html = _update(state)["html"]
    assert "Last successful check: 2026-11-13T10:30:00Z" in html
    assert 'id="update-status-heading"' in html
    assert '<th scope="col">Details</th>' in html
    assert "Build details" not in html and "Version information" not in html
    assert "<summary>Updating ROMarr with Docker</summary>" in html
    assert "Settings → General" in html


def test_update_page_css_is_scoped_and_responsive():
    """Reuse app theme tokens and retain narrow-screen plugin readability."""
    css = ui.CSS
    assert ".update-hero{" in css
    assert ".update-plugin-table td::before" in css
    assert ".update-install-table" in css and "max-width:1120px" in css
    assert "@media(max-width:440px)" in css
    assert "var(--accent-text)" in css
    assert "var(--surface)" in css


def test_stats_banner_requires_real_availability_and_effective_capability():
    """Rendered Stats wording must respect Docker's inability to self-apply."""
    stats = {"version": "1.8.1"}
    status = _payload(check_status={"state": "available"},
                      update_available=True)
    banner = _stats_banner(stats, status)
    assert "Update available" in banner and "Docker cannot apply" in banner
    assert "applies on the next daily check" not in banner
    assert _stats_banner(stats, _payload(check_status={"state": "current"})) == ""


def test_stats_banner_explains_disabled_scheduled_checks():
    """An available release does not turn a disabled scheduler back on."""
    stats = {"version": "1.8.1"}
    state = _payload(check_status={"state": "available"},
                     install={"kind": "git", "can_apply": True},
                     settings={"auto_update": True,
                               "auto_update_effective": False,
                               "update_check": False})
    banner = _stats_banner(stats, state)
    assert "Scheduled update checks are disabled" in banner
    assert "applies on the next daily check" not in banner


def test_stats_banner_handles_failed_and_mismatched_status():
    """Do not reuse a stale or mismatched Update API verdict as current."""
    stats = {"version": "1.8.1"}
    assert "Update status: error" in _stats_banner(
        stats, _payload(check_status={"state": "error"}))
    assert "Update status unavailable" in _stats_banner(
        stats, _payload(running_version="1.8.2"))
    assert "Update status unavailable" in _stats_banner(stats, None)


def test_update_ignores_late_api_response_after_navigation():
    """A previous page's fetch must not repaint an unrelated newer page."""
    start = ui.JS.index("let updatePollGeneration=0;")
    stop = ui.JS.index("RENDER.logs=async()=>", start)
    setup = _BASE.replace(
        "const j=async()=>data;",
        "let activePage='update',pageVersion=1,resume;"
        "const j=()=>new Promise(resolve=>{resume=resolve;});",
    )
    script = setup + _helpers() + ui.JS[start:stop] + """
const pending=RENDER.update();
root.innerHTML='<div>New page</div>';
activePage='status';pageVersion=2;
resume(data);
pending.then(()=>console.log(JSON.stringify(root.innerHTML)))
  .catch(e=>{console.error(String(e));process.exitCode=1;});
"""
    assert json.loads(_node(script, _payload())) == "<div>New page</div>"


def test_stats_ignores_late_update_response_after_navigation():
    """An extra Stats update-status fetch must respect page generation."""
    start = ui.JS.index("RENDER.stats=async()=>")
    stop = ui.JS.index("RENDER.queue=async()=>", start)
    setup = _BASE.replace(
        "const j=async()=>data;",
        "let activePage='stats',pageVersion=1,resume;"
        "const j=url=>url==='/api/v1/stats'?Promise.resolve(data.stats)"
        ":url==='/api/v1/update'?new Promise(resolve=>{resume=resolve;})"
        ":Promise.reject(new Error('optional audit unavailable'));",
    )
    script = setup + _helpers() + ui.JS[start:stop] + """
const pending=RENDER.stats();
root.innerHTML='<div>New page</div>';
activePage='status';pageVersion=2;
resume(data.update);
pending.then(()=>console.log(JSON.stringify(root.innerHTML)))
  .catch(e=>{console.error(String(e));process.exitCode=1;});
"""
    assert json.loads(_node(script, {
        "stats": {"version": "1.8.1"},
        "update": _payload(),
    })) == "<div>New page</div>"


def test_status_ignores_late_health_response_after_navigation():
    """Health data arriving late must not repaint another page."""
    start = ui.JS.index("RENDER.status=async()=>")
    stop = ui.JS.index("\n};\n", start) + 4
    setup = _BASE.replace(
        "const j=async()=>data;",
        "let activePage='status',pageVersion=1,resume;"
        "const j=()=>new Promise(resolve=>{resume=resolve;});",
    )
    script = setup + _helpers() + ui.JS[start:stop] + """
const pending=RENDER.status();
root.innerHTML='<div>New page</div>';
activePage='update';pageVersion=2;
resume(data);
pending.then(()=>console.log(JSON.stringify(root.innerHTML)))
  .catch(e=>{console.error(String(e));process.exitCode=1;});
"""
    assert json.loads(_node(script, {"version": "1.8.1"})) == "<div>New page</div>"


def test_stats_and_status_use_same_verified_build_presentation():
    """Cross-page UI should share one escaped build-identity presenter."""
    source = ui.JS
    assert "buildIdentityLine(h.build)" in source
    assert "const build=d.build||{}" in source
    assert "up.running_version===s.version?up.build:null" in source
    for marker in ("RENDER.stats=async()=>", "RENDER.status=async()=>",
                   "RENDER.update=async()=>", "RENDER.queue=async()=>"):
        assert marker in source


def test_update_nightly_identity_and_conditional_revision():
    """Only official main-branch provenance identifies the nightly source."""
    sha = "a" * 40
    nightly = {"type": "development", "source_ref": "refs/heads/main",
               "source_revision": sha, "source_repository": "BlizzHacker/romarr"}
    html = _update(_payload(build=nightly,
                           settings={"update_channel": "nightly"},
                           check_status={"state": "unknown",
                                         "reason": "nightly_revision_not_checked"}))["html"]
    assert "Build type <b>Nightly</b>" in html
    assert "Source revision <code>aaaaaaaa</code>" in html
    for other in (
        {"type": "release", "source_ref": "refs/tags/v1.8.1",
         "source_revision": sha, "source_repository": "BlizzHacker/romarr"},
        {"type": "development", "source_ref": "refs/pull/21/head",
         "source_revision": sha, "source_repository": "BlizzHacker/romarr"},
        {"type": "development", "source_ref": "refs/heads/main",
         "source_revision": sha, "source_repository": "TenchiMisaki/romarr"},
    ):
        output = _update(_payload(build=other))["html"]
        assert "Source revision <code>" not in output
    assert "Build type <b>Release</b>" in _update(_payload(build={
        "type": "release", "source_ref": "refs/tags/v1.8.1",
        "source_revision": sha, "source_repository": "BlizzHacker/romarr"}))["html"]


def test_update_installation_table_and_plugin_button_position():
    """Show three aligned columns and keep plugin action in its own card."""
    html = _update(_payload(plugins={
        "sample": {"source": "example/repo", "ref": "main", "commit": "abcdef123456"},
    }))["html"]
    for column in ("Setting", "Status", "Details"):
        assert '<th scope="col">' + column + '</th>' in html
    assert '<table class="update-install-table">' in html
    assert html.index('id="update-plugins-heading"') < html.index('id="up-plugins"')
    assert html.index('id="up-plugins"') < html.index('<table class="update-plugin-table">')
    assert 'id="up-plugin-msg"' in html
    assert 'id="up-msg"' in html
    assert "Version information" not in html
    empty = _update(_payload(plugins={}))["html"]
    assert 'id="up-plugins"' not in empty and 'id="up-plugin-msg"' not in empty
    assert 'id="up-msg"' in empty


def test_update_nightly_does_not_fake_stable_comparison():
    """Never show an available stable release as a nightly update verdict."""
    html = _update(_payload(
        build={"type": "development", "source_ref": "refs/heads/main",
               "source_repository": "BlizzHacker/romarr",
               "source_revision": "b" * 40},
        settings={"update_channel": "nightly"},
        check_status={"state": "available"},
    ))["html"]
    assert '<h2 id="update-status-heading">Update status unknown</h2>' in html
    assert '<div class="update-version is-new">' not in html


@pytest.mark.parametrize("outcome", ["success", "failure", "refresh"])
def test_update_command_completion_ignores_stale_page(outcome):
    """Old plugin callbacks cannot update or refresh a new page generation."""
    start = ui.JS.index("let updatePollGeneration=0;")
    stop = ui.JS.index("RENDER.logs=async()=>", start)
    setup = _BASE.replace(
        "const j=async()=>data;",
        "let activePage='update',pageVersion=1,resolveCommand,rejectCommand;"
        "const j=(url,opts)=>opts?new Promise((resolve,reject)=>"
        "{resolveCommand=resolve;rejectCommand=reject;}):Promise.resolve(data);",
    ).replace(
        "const toast=()=>{},go=()=>{},confirm=()=>false;",
        "const toast=()=>{},refreshes=[],timers=[];"
        "const go=page=>refreshes.push(page),confirm=()=>false;"
        "const setTimeout=fn=>timers.push(fn);",
    )
    script = setup + _helpers() + ui.JS[start:stop] + """
(async()=>{
  await RENDER.update();
  const old=controls['#up-plugins'];
  const pending=old.onclick({target:old});
  if(data.case==='refresh'){
    resolveCommand({ok:true,message:'Old result'});
    await pending;
    activePage='status';pageVersion++;
    root.innerHTML='<div>Elsewhere</div>';
    for(const fn of timers)fn();
    console.log(JSON.stringify({html:root.innerHTML,refreshes}));
    return;
  }
  activePage='status';pageVersion++;
  root.innerHTML='<div>Elsewhere</div>';
  activePage='update';pageVersion++;
  for(const key of ['#up-plugin-msg','#up-msg','#up-plugins','#up-check'])
    delete controls[key];
  await RENDER.update();
  const current=$('#up-plugin-msg'),before=current.innerHTML;
  if(data.case==='failure')rejectCommand(new Error('Old failure'));
  else resolveCommand({ok:true,message:'Old result'});
  await pending;
  for(const fn of timers)fn();
  console.log(JSON.stringify({before,after:current.innerHTML,refreshes}));
})().catch(error=>{console.error(String(error));process.exitCode=1});
"""
    payload = _payload(plugins={"sample": {
        "source": "example/repo", "ref": "main", "commit": "abcdef123456",
    }})
    payload["case"] = outcome
    result = json.loads(_node(script, payload))
    assert result["refreshes"] == []
    if outcome == "refresh":
        assert result["html"] == "<div>Elsewhere</div>"
    else:
        assert result["before"] == result["after"]

@pytest.mark.parametrize("phase", ["health", "formats"])
def test_status_overlapping_refreshes_keep_newest_result(phase):
    """Overlapping Status renders must not let an earlier response win."""
    start = ui.JS.index("RENDER.status=async()=>")
    stop = ui.JS.index("\n};\n", start) + 4
    setup = r"""
const data=JSON.parse(process.argv[1]);
const root={innerHTML:''},controls={},RENDER={};
let activePage='status',pageVersion=1;
const $=selector=>selector==='#page'?root:(controls[selector]??={
  innerHTML:'',textContent:'',style:{},value:'',querySelectorAll:()=>[]
});
const esc=s=>String(s??'');
const buildIdentityLine=()=>'',ggrequestzCard=()=>'';
const playCard=()=>'',moonlightCard=()=>'';
const wireGGRequestz=()=>{},wireMoonlight=()=>{};
const health=[],formats=[];
const j=url=>new Promise(resolve=>{
  if(url==='/api/v1/system/status')health.push(resolve);
  else if(url==='/api/v1/frontend/formats')formats.push(resolve);
  else throw Error('unexpected request '+url);
});
"""
    exercise = r"""
(async()=>{
  const oldRender=RENDER.status();
  let latestRender;
  if(data.phase==='health'){
    latestRender=RENDER.status();
    health[1]({version:'CURRENT-VERSION'});await Promise.resolve();
    health[0]({version:'STALE-VERSION'});await Promise.resolve();
    const ok=root.innerHTML.includes('CURRENT-VERSION')
      &&!root.innerHTML.includes('STALE-VERSION');
    for(const finish of formats)finish({formats:[]});
    await Promise.all([oldRender,latestRender]);
    return ok;
  }
  health[0]({version:'STALE-VERSION'});await Promise.resolve();
  latestRender=RENDER.status();
  health[1]({version:'CURRENT-VERSION'});await Promise.resolve();
  formats[1]({formats:[{name:'current',label:'CURRENT-FORMAT'}]});
  await Promise.resolve();
  formats[0]({formats:[{name:'stale',label:'STALE-FORMAT'}]});
  await Promise.resolve();
  await Promise.all([oldRender,latestRender]);
  return controls['#fe-row'].innerHTML.includes('CURRENT-FORMAT')
    &&!controls['#fe-row'].innerHTML.includes('STALE-FORMAT');
})().then(ok=>console.log(JSON.stringify({ok})))
  .catch(e=>{console.error(String(e));process.exitCode=1;});
"""
    script = setup + ui.JS[start:stop] + exercise
    assert json.loads(_node(script, {"phase": phase}))["ok"]

def test_nightly_update_page_shows_verified_revisions_without_stable_tag_fallback():
    """The redesigned hero uses official revision SHAs, not a stale release tag."""
    running, latest = "a" * 40, "b" * 40
    html = _update(_payload(
        running_version="0.0.0+unknown", latest_version="1.8.1",
        build={"type": "development", "source_repository": "BlizzHacker/romarr",
               "source_ref": "refs/heads/main", "source_revision": running},
        check_status={"state": "available", "channel": "nightly",
                      "running_revision": running, "latest_revision": latest},
        settings={"update_channel": "nightly", "auto_update": True,
                  "auto_update_effective": False},
    ))["html"]
    assert '<h2 id="update-status-heading">Update available</h2>' in html
    assert "<dt>Installed version</dt><dd>Nightly · aaaaaaaa</dd>" in html
    assert "<dt>Latest on GitHub</dt><dd>bbbbbbbb</dd>" in html
    assert "A newer official Nightly revision was verified" in html
    assert "<dd>1.8.1</dd>" not in html
    assert 'id="up-apply"' not in html


def test_nightly_current_display_does_not_claim_an_update():
    """An equal official-main SHA is displayed as current without a warning."""
    sha = "c" * 40
    html = _update(_payload(
        running_version="0.0.0+unknown", latest_version="1.8.1",
        build={"type": "development", "source_repository": "BlizzHacker/romarr",
               "source_ref": "refs/heads/main", "source_revision": sha},
        check_status={"state": "current", "channel": "nightly",
                      "running_revision": sha, "latest_revision": sha},
        settings={"update_channel": "nightly", "update_check": True},
    ))["html"]
    assert '<h2 id="update-status-heading">You\'re up to date</h2>' in html
    assert "<dt>Installed version</dt><dd>Nightly · cccccccc</dd>" in html
    assert "<dt>Latest on GitHub</dt><dd>cccccccc</dd>" in html
    assert '<div class="update-version is-new">' not in html
    assert "<dd>1.8.1</dd>" not in html


def test_nightly_missing_metadata_does_not_make_release_current():
    """Unknown Nightly status must not surface a retained stable release tag."""
    html = _update(_payload(
        running_version="0.0.0+unknown", latest_version="1.8.1",
        check_status={"state": "unknown", "channel": "nightly",
                      "reason": "nightly_build_unverified"},
        settings={"update_channel": "nightly", "auto_update": False},
    ))["html"]
    assert '<h2 id="update-status-heading">Update status unknown</h2>' in html
    assert "Could not verify Nightly availability" in html
    assert "<dt>Latest on GitHub</dt><dd>—</dd>" in html
    assert "<dd>1.8.1</dd>" not in html


def test_stats_nightly_banner_reports_revisions_not_release_versions():
    """Stats must not describe a Nightly check as a stable release update."""
    running, latest = "a" * 40, "b" * 40
    update = _payload(
        running_version="0.0.0+unknown", latest_version="1.8.1",
        check_status={"state": "available", "channel": "nightly",
                      "running_revision": running, "latest_revision": latest})
    banner = _stats_banner({"version": "0.0.0+unknown"}, update)
    assert "Nightly revision" in banner and "bbbbbbbb" in banner
    assert "aaaaaaaa" in banner
    assert "1.8.1 is available" not in banner


def test_update_page_observes_initial_check_without_posting_commands():
    """Observe the scheduled Nightly check and repaint without manual action."""
    start = ui.JS.index("let updatePollGeneration=0;")
    stop = ui.JS.index("RENDER.logs=async()=>", start)
    setup = _BASE.replace(
        "const j=async()=>data;",
        "let reads=0,posts=0;"
        "const j=async(url,options)=>{if(options){posts++;throw Error('unexpected POST');}"
        "reads++;return reads===1?data.before:data.after;};",
    ).replace(
        "const toast=()=>{},go=()=>{},confirm=()=>false;",
        "let activePage='update',pageVersion=1;const timers=[];"
        "const setTimeout=fn=>{timers.push(fn);return timers.length;};"
        "const toast=()=>{},go=()=>{},confirm=()=>false;",
    )
    script = setup + _helpers() + ui.JS[start:stop] + """
(async()=>{
  await RENDER.update();
  const initiallyUnknown=root.innerHTML.includes('Update status unknown');
  if(!timers.length)throw Error('automatic status refresh not scheduled');
  await timers.shift()();
  await new Promise(resolve=>setImmediate(resolve));
  console.log(JSON.stringify({
    initiallyUnknown, updated:root.innerHTML.includes("You're up to date"),
    latest:root.innerHTML.includes("<dd>aaaaaaaa</dd>"), reads, posts
  }));
})().catch(error=>{console.error(String(error));process.exitCode=1});
"""
    sha = "a" * 40
    before = _payload(
        running_version="0.0.0+unknown", latest_version="1.8.1",
        build={"type": "development", "source_ref": "refs/heads/main",
               "source_revision": sha, "source_repository": "BlizzHacker/romarr"},
        check_status={"state": "unknown", "channel": "nightly",
                      "reason": "build_or_channel_changed",
                      "running_revision": sha},
        settings={"update_channel": "nightly", "update_check": True},
    )
    after = {**before, "check_status": {
        "state": "current", "channel": "nightly",
        "running_revision": sha, "latest_revision": sha,
        "last_attempt_at": "2026-11-14T21:45:00Z"}}
    result = json.loads(_node(script, {"before": before, "after": after}))
    assert result == {"initiallyUnknown": True, "updated": True,
                      "latest": True, "reads": 3, "posts": 0}


def test_update_page_automatic_observation_respects_disabled_schedule():
    """Do not poll or manually initiate checks when auto-check is disabled."""
    start = ui.JS.index("let updatePollGeneration=0;")
    stop = ui.JS.index("RENDER.logs=async()=>", start)
    setup = _BASE.replace(
        "const toast=()=>{},go=()=>{},confirm=()=>false;",
        "let activePage='update',pageVersion=1;const timers=[];"
        "const setTimeout=fn=>timers.push(fn);"
        "const toast=()=>{},go=()=>{},confirm=()=>false;",
    )
    script = setup + _helpers() + ui.JS[start:stop] + """
RENDER.update().then(()=>console.log(JSON.stringify({
  timers:timers.length,unknown:root.innerHTML.includes('Update status unknown')
}))).catch(error=>{console.error(String(error));process.exitCode=1});
"""
    result = json.loads(_node(script, _payload(
        check_status={"state": "unknown", "reason": "build_or_channel_changed"},
        settings={"update_channel": "nightly", "update_check": False},
    )))
    assert result == {"timers": 0, "unknown": True}


def test_update_page_abandons_old_poll_after_navigation():
    """Background status checks may not overwrite a different page."""
    start = ui.JS.index("let updatePollGeneration=0;")
    stop = ui.JS.index("RENDER.logs=async()=>", start)
    setup = _BASE.replace(
        "const toast=()=>{},go=()=>{},confirm=()=>false;",
        "let activePage='update',pageVersion=1;const timers=[];"
        "const setTimeout=fn=>timers.push(fn);"
        "const toast=()=>{},go=()=>{},confirm=()=>false;",
    )
    script = setup + _helpers() + ui.JS[start:stop] + """
(async()=>{
  await RENDER.update();
  const scheduled=timers.length;
  activePage='status';pageVersion=2;
  root.innerHTML='<div>Another page</div>';
  await timers.shift()();
  console.log(JSON.stringify({scheduled,html:root.innerHTML}));
})().catch(error=>{console.error(String(error));process.exitCode=1});
"""
    result = json.loads(_node(script, _payload(
        check_status={"state": "unknown", "reason": "nightly_revision_not_checked"},
        settings={"update_check": True},
    )))
    assert result == {"scheduled": 1, "html": "<div>Another page</div>"}
