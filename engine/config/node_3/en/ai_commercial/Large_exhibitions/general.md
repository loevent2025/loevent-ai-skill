# AI Commercial · Large Exhibitions / Expo · Venue Selection Criteria Knowledge Base

## Scale Quick Reference

| Scale Level | Headcount | Typical Scenarios |
|-------------|-----------|-------------------|
| Mid-Size Exhibition | 300–800 | Regional AI expo, vertical industry AI exhibition |
| Large Exhibition | 800–2,000 | National AI technology exhibition, industry ecosystem conference |
| Major Industry Event | 2,000+ | International AI summit, annual technology expo |

---

## Functional Zone Reference

All functional zones in a large exhibition must operate simultaneously without interfering with one another. When selecting a venue, confirm that each zone's area, network, and power supply can be independently guaranteed.

| Functional Zone | Area Share | Core Configuration Requirements |
|-----------------|------------|--------------------------------|
| Main Exhibition Hall | 40–50% | Mix of standard and custom-built booths; aisle width between booths ≥ 2 m |
| Main Stage / Keynote Area | 15–20% | Professional AV system, LED screens, independently controllable lighting |
| Demo Experience Zone | 15–20% | Independent network circuit, multi-device parallel operation, queuing flow design |
| Business Meeting Area | 10–15% | Physical soundproofing or semi-isolation, booking system support, relatively quiet |
| Rest / Dining Area | 10% | Dedicated zone, not shared with exhibition areas, charging facilities available |

---

# Selection Criteria

---

## Criterion 1: Network & Technical Infrastructure (Primary Hard Requirement)

**Definition:**
Network risk at AI Commercial large exhibitions centers on two points: first, the instantaneous peak bandwidth consumption when numerous booths run live demos simultaneously; second, demo failures caused by firewalls blocking access to large language model APIs. What makes exhibitions uniquely high-stakes is that failures are public—on-site attendees and media witness them directly, causing significant brand damage.

**Evaluation Areas:**

Network Bandwidth & Concurrency
- Total bandwidth ≥ 1 Gbps (2 Gbps recommended for 2,000+ attendees)
- Support for 500+ devices making simultaneous high-frequency API calls
- Wired backbone network covering all booth areas (Wi-Fi alone is insufficient)
- Wired access points in the booth area: independent wired connection per booth
- Venue-wide Wi-Fi coverage with no dead zones; independent access points configured per zone

Access Permissions (Core AI Commercial Requirement)
- No port restrictions, no firewall blocking
- Unrestricted access to major AI cloud services: OpenAI, Anthropic, Azure OpenAI, Google Vertex AI, AWS Bedrock
- Unrestricted access to development dependencies and CDNs (required for demo interface loading)
- Exhibitors permitted to bring their own routers or 4G/5G hotspots as independent backups

Segmented Network Isolation
- Independent network circuit for the main stage/keynote area (prevents booth traffic from impacting main stage demos)
- Independent network circuit for the demo experience zone (ensures stability for core experience showcases)
- Independent network for the business meeting area (video conferencing and remote demo requirements)

Backup Plans
- Venue equipped with high-power 4G/5G signal amplification
- Dedicated standalone hotspot backups for key booths (custom-built booths, main demo area)
- Clearly defined network failure response time commitments (SLA)

Power (Hard Requirement on Par with Network)
- Standard booths: independent power per booth, ≥ 4 outlets, single-phase 10A
- Custom-built booths: independent circuit supporting high-power equipment (power consumption must be declared in advance)
- Demo experience zone: independent power circuit supporting multiple high-performance devices running simultaneously
- Main stage: independent power supply supporting professional AV equipment at full capacity
- Total venue electrical load must be specified, with confirmation that full-venue operation at maximum load is supported

## Criterion 2: Exhibition Space Structure & Load Capacity (Hard Requirement)

**Definition:**
Space requirements for large exhibitions are highly complex: keynote presentations, static booth displays, interactive product experiences, and business meetings all happen concurrently, with attendee traffic flowing continuously between zones. The spatial structure must support this compound operation while ensuring each zone's independence and accessibility.

**Evaluation Areas:**

Main Exhibition Hall
- Clear height ≥ 6 m (to support custom-built booth construction, including lighting trusses)
- Floor load capacity ≥ 500 kg/m² (for large equipment and booth structures)
- Aisle width in booth areas ≥ 2 m (bidirectional traffic during peak flow)
- Level flooring suitable for carpet/flooring installation (basic requirement for booth construction)
- Forklift or freight elevator access during setup (essential for transporting large exhibition materials)

Main Stage / Keynote Area
- Physically separate space with sound isolation or semi-isolation from the exhibition hall
- Stage clear depth ≥ 8 m, clear width ≥ 12 m (to accommodate speaker + backdrop + side screens)
- Audience area capacity matched to attendee count (based on comfortable capacity, not maximum occupancy)
- Rigging points or truss structures to support professional lighting and large screen installation

Demo Experience Zone
- Dedicated area with a clearly defined flow (queuing area → experience area → exit)
- Each experience station ≥ 4 m² (including queuing buffer zone)
- Support for multi-device parallel operation (independent power + network)
- Controllable lighting (to prevent strong ambient light from impairing screen visibility)

Business Meeting Area
- Relatively quiet, with physical or acoustic isolation from the main stage and exhibition hall
- Configurable with independent tables and seating (≥ 8–10 meeting units)
- Brand signage placement permitted

Attendee Flow & Circulation
- Main entrance capacity matched to attendee count (no bottlenecks during peak entry)
- Clear wayfinding system for functional zones (or permission for the organizer to install their own signage)
- Emergency evacuation routes unobstructed and not impacting booth layouts

---

## Criterion 3: Main Stage AV System Capabilities (Hard Requirement)

**Definition:**
The main stage at an AI Commercial exhibition is the central node for brand messaging and technology showcasing. Keynote quality and visual presentation directly represent the organizer's brand image. The professionalism of the AV system is something that cannot be compensated for by "making do."

**Evaluation Areas:**

Screens & Displays
- LED screen pixel pitch ≤ P2.5 (close-range viewing clarity), resolution supporting 4K
- Dual-screen output support (speaker preview screen + audience main screen)
- Screen size matched to the maximum viewing distance in the audience area (content must be clearly visible to the farthest attendees)
- Multi-source video signal switching support (seamless transitions between keynote slides, live demos, and video playback)

Audio System
- Professional line array speakers with full-venue, dead-zone-free coverage
- Audio system supporting both speech and music modes
- ≥ 4 wireless microphones (host, speaker, backups)
- No significant echo or feedback risk (venue reverberation time requires assessment)

Lighting System
- Stage lighting independently controlled, supporting transitions between keynote and showcase modes
- Separate lighting zone control for stage area and audience area
- No significant glare interference from ambient light on the main screen

Livestreaming & Recording
- Venue structure supports multi-camera setup (with stable mounting positions)
- External livestreaming equipment access permitted
- Network supports HD livestream broadcasting (dedicated bandwidth, not shared with booth traffic)

---

## Criterion 4: AI Product Live Demo Support Capabilities (Hard Requirement)

**Definition:**
The core value of an AI Commercial exhibition lies in enabling attendees to experience AI product capabilities firsthand. A failed live demo not only impacts a single booth—the negative impression spreads rapidly among attendees. Technical reliability in the demo zone directly determines the exhibition's reputation.

**Evaluation Areas:**

Demo Zone Base Configuration
- Dedicated demo experience zone, physically separated from standard booth areas
- Each experience station with independent power and independent network circuit
- High-definition display equipment (≥ 55 inches, resolution ≥ 1080p, suitable for group viewing)
- Controllable lighting (to prevent strong ambient light from causing screen glare)
- Clearly designed queuing flow (to prevent crowding from degrading the experience)

AI Product-Specific Requirements
- Unrestricted network access to all major AI cloud services (see Criterion 1)
- Stable network latency (large model streaming output and real-time agent responses are latency-sensitive)
- Support for multi-tab/multi-window side-by-side display (demo interface, backend logs, output results)
- Screen mirroring with high refresh rate support (streaming AI-generated content output quality depends on frame rate)
- On-site screen recording and external publishing permitted

Backup Support
- Venue permits exhibitors to bring backup equipment (secondary computer, backup network)
- Technical support personnel available for rapid response to equipment failures during the exhibition

---

## Criterion 5: AI Commercial Industry Alignment (High-Weight Criterion)

**Definition:**
AI Commercial large exhibitions attract a complex mix of attendees: developers, enterprise technology decision-makers, investors, and media. The venue must simultaneously satisfy "developers finding it technically compelling" and "enterprise clients finding it sufficiently professional"—this is the core tension in AI Commercial exhibition positioning.

**AI Commercial Exhibition Positioning:**
> Professional enough for enterprise clients to feel confident signing deals
> Tech-forward enough for developers to engage in deep technical exchange
> Design-forward enough for media to want to photograph and share

**✅ Suitable Venue Types:**
- Professional convention and exhibition centers (ample space, comprehensive amenities, load capacity and clear height meeting custom-built booth requirements)
- Tech park dedicated exhibition halls (strong technology atmosphere, high industry relevance)
- Upscale hotel ballroom complexes (suitable for mid-size boutique exhibitions, high service quality)
- Modern urban landmark venues (strong design appeal, effective media distribution)

**❌ Venue Types to Avoid:**
- Outdated convention centers (inadequate infrastructure; network and power unlikely to meet AI exhibition demands)
- Commercial mall event spaces (excessive retail atmosphere conflicts with technology exhibition positioning)
- Large warehouses without HVAC or with insufficient ventilation (high attendee volume and equipment heat output make climate control a mandatory requirement)

---

## Criterion 6: Capacity & Crowd Comfort Management (Hard Requirement)

**Definition:**
Crowd management is a critical variable in venue selection for large exhibitions. Overcrowding not only degrades the experience but also directly impacts AI product demo effectiveness (excessive crowds around stations cause device overheating and network congestion).

**Area Reference Standards:**

| Exhibition Mode | Area per Person |
|----------------|-----------------|
| Exhibition touring (mobile) | 1.5–2 m² |
| Main stage keynote (fixed seating) | 1–1.2 m² |
| Demo experience zone (interactive) | 3–4 m² |

**Evaluation Areas:**
- Base calculations on comfortable capacity, not the venue's maximum occupancy
- Whether the HVAC system can handle simultaneous cooling demands from high attendee volume and dense equipment heat output
- Independent climate control for each functional zone (stage lighting areas generate significant heat, creating temperature differentials with booth areas)
- Restroom count (recommend 2 per 100 attendees; requires thorough verification for large exhibitions)
- Entry point crowd distribution capacity (no extended queuing during peak entry periods)

---

## Criterion 7: Setup & Teardown Conditions (Hard Requirement)

**Definition:**
Setup for large exhibitions typically requires 2–3 days, with teardown requiring 1–2 days. The venue's support for setup operations directly impacts whether the exhibition can open on schedule and the overall exhibitor experience.

**Evaluation Areas:**

Setup Conditions
- Venue access permitted 3–5 days in advance for setup (standard exhibition requirement)
- Freight corridors and freight elevators available (to support transport of large booth structures and equipment)
- Floor capable of supporting forklift operations
- Independent water and power access available during setup
- Venue provides setup specifications (clear height limits, rigging regulations, power declaration process)

Teardown Conditions
- Teardown timeline clearly defined (no less than 1 day)
- Freight corridors during teardown operate independently from exhibition-period logistics
- Venue waste removal capacity sufficient for the event

Technical Support
- Number and responsiveness of venue on-site technical staff
- Committed response times for water and power failures
- Network failure backup contingency plans

---

## Criterion 8: Transportation & Arrival Accessibility (High-Weight Criterion)

**Definition:**
Attendees at large exhibitions come from various locations, and transportation accessibility directly affects turnout and experience. Parking and large-scale material transport are transportation needs unique to large exhibitions.

**Evaluation Areas:**
- Distance from the city center or major transportation hubs (airport/high-speed rail station)
- Direct metro access or convenient shuttle connections (public transit is the primary choice for most attendees)
- Parking capacity (exhibitor, VIP guest, and media parking needs)
- Loading/unloading areas accessible to large freight vehicles
- Nearby hotel availability (accommodation needs for exhibitors and out-of-town attendees)
- Clear venue entrance signage with strong multi-entrance crowd distribution capacity

---

## Criterion 9: Branding & Media Support Capabilities (High-Weight Criterion)

**Definition:**
The brand distribution value of an AI Commercial exhibition is equally important as the on-site experience. The venue's visual conditions and media support capabilities directly affect the event's secondary distribution impact.

**Evaluation Areas:**
- Sufficient space at the main entrance/main stage area for large-scale brand installations
- Designated photo-worthy areas suitable for social media distribution
- Venue natural lighting or artificial lighting suitable for professional photography
- Full-event media filming and livestreaming permitted
- Media reception area (media registration, interview rooms)
- Whether the venue operator has owned media channels or official social accounts (joint distribution as a bonus)
- Long-term or annual reuse permitted (building venue-associated brand event recognition)

---

## Criterion 10: Ancillary Services & Support Capabilities (High-Weight Criterion)

**Definition:**
Large exhibitions run for extended periods (typically 1–3 days), and the basic service needs of exhibitors and attendees must be reliably met. Insufficient ancillary services directly impact the exhibition's reputation.

**Evaluation Areas:**

Dining
- Adequate food and beverage supply within or immediately adjacent to the venue (estimated based on attendee count to avoid extended queuing)
- Organizer permitted to bring external catering teams on-site
- Tea break area capable of providing all-day beverages and light refreshments

Business Amenities
- Sufficient hotel accommodation within or near the venue (for exhibitors and speakers)
- Dedicated VIP reception area or VIP lounge
- Courier/logistics receiving services (for exhibitor material shipments)

On-Site Services
- Venue cleaning conducted on a regular schedule throughout the exhibition
- Security staff count and coverage capacity matched to event scale
- On-site first aid station or emergency medical personnel available

---

## Criterion 11: Operational Compliance & Usage Restrictions (Flexible Criterion)

**Definition:**
Large exhibitions involve numerous external exhibitors, media, and livestreaming equipment. Usage restrictions must be thoroughly investigated in advance to prevent compliance obstacles from arising during the exhibition.

**Evaluation Areas:**
- Whether maximum occupancy is clearly defined and meets requirements
- Whether large-scale public commercial exhibitions are permitted
- Whether external setup teams are allowed on-site for construction
- Whether external catering teams are permitted on-site
- Whether livestreaming and recording permissions are subject to restrictions
- Whether venue liability insurance coverage is clearly defined
- Large event filing requirements (venue operators can typically provide support)

---

# Default Priority Ranking

## Hard Requirements (Disqualify Immediately if Unmet)
1. Network & Technical Infrastructure (bandwidth, AI API access, segmented independent networks)
2. Exhibition Space Structure & Load Capacity (clear height, floor load, zone independence)
3. Main Stage AV System Capabilities
4. AI Product Live Demo Support Capabilities
5. Capacity & Crowd Comfort Management
6. Setup & Teardown Conditions

## High-Weight Criteria (Strongly Influence Decision)
7. AI Commercial Industry Alignment
8. Transportation & Arrival Accessibility
9. Branding & Media Support Capabilities
10. Ancillary Services & Support Capabilities

## Flexible Criteria (Evaluate Based on Specific Circumstances)
11. Operational Compliance & Usage Restrictions

---

# Hybrid Scenario Handling Guidelines

### Exhibition + Themed Summit (Co-Located)
- Upgrade main stage AV system to flagship level (professional lighting director, multi-camera livestreaming)
- Keynote area and exhibition hall require clear temporal or spatial separation
- Additional network bandwidth required (simultaneous summit keynote livestreaming + exhibition demos)
- Separate guest/media corridors from general attendee corridors

### Exhibition + Product Launch (Co-Located)
- Upgrade main stage to product launch caliber (stage design, lighting director)
- Product launch segment requires independent crowd control (separate attendees from invited audience)
- Branding capabilities elevated to top priority
- Dedicated media zone planning required (media seating, interview area, livestream camera positions)

### Mid-Size Boutique Exhibition (300–800 Attendees)
- Upscale hotel ballroom complexes are a viable option (high service quality, but setup conditions require thorough verification)
- Clear height requirements in setup conditions can be relaxed (no large custom-built booths)
- Demo experience zone may be merged with the booth area, but independent network must be guaranteed
- Ancillary services can leverage the hotel's own service capabilities, reducing external coordination costs